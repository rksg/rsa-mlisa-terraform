#!/bin/bash

# Script to swap dataproc cluster state after migration
# This moves the "migration" cluster to become "production"
# Usage: ./migrate_dpccluster_state.sh [environment] [cluster] [target-site]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed or not in PATH"
    exit 1
fi

# Parse arguments
AUTO_APPLY=false
ENVIRONMENT=""
CLUSTER=""
TARGET_SITE=""

# Parse arguments and flags
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-apply)
            AUTO_APPLY=true
            shift
            ;;
        -h|--h|--help)
            echo "Usage: $0 <environment> <cluster> [options]"
            echo ""
            echo "Arguments (REQUIRED):"
            echo "  environment    Environment name (e.g., beta, stg, qa, prod-us, prod-eu, prod-asia, dev)"
            echo "  cluster        Cluster type (e.g., rai, r1-rai)"
            echo ""
            echo "Options:"
            echo "  --auto-apply   Automatically run 'terraform apply' after state migration"
            echo "  -h, --h, --help   Show this help message"
            echo ""
            echo "Note: This script only works for PRIMARY site (not DR)"
            echo "      Workspace format: <environment>-<cluster>-primary"
            echo ""
            echo "Examples:"
            echo "  $0 beta rai"
            echo "  $0 stg r1-rai --auto-apply"
            echo "  $0 qa rai"
            echo "  $0 --help"
            echo ""
            exit 0
            ;;
        beta|stg|qa|prod-us|prod-eu|prod-asia|dev)
            if [ -z "$ENVIRONMENT" ]; then
                ENVIRONMENT=$1
            else
                print_error "Environment specified multiple times: '$ENVIRONMENT' and '$1'"
                echo ""
                echo "Run '$0 --help' for usage information"
                exit 1
            fi
            shift
            ;;
        rai|r1-rai)
            if [ -z "$CLUSTER" ]; then
                CLUSTER=$1
            else
                print_error "Cluster specified multiple times: '$CLUSTER' and '$1'"
                echo ""
                echo "Run '$0 --help' for usage information"
                exit 1
            fi
            shift
            ;;
        primary|dr)
            # TARGET_SITE is always primary for this script, but handle dr gracefully
            if [ "$1" != "primary" ]; then
                print_warning "Ignoring target-site '$1'. This script only works for 'primary' site."
            fi
            shift
            ;;
        *)
            print_error "Unknown argument: '$1'"
            echo ""
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$ENVIRONMENT" ]; then
    print_error "ERROR: Environment argument is required"
    echo ""
    echo "Run '$0 --help' for usage information"
    exit 1
fi

if [ -z "$CLUSTER" ]; then
    print_error "ERROR: Cluster argument is required"
    echo ""
    echo "Run '$0 --help' for usage information"
    exit 1
fi

# TARGET_SITE is always primary for this script
TARGET_SITE="primary"

WORKSPACE_NAME="${ENVIRONMENT}-${CLUSTER}-${TARGET_SITE}"

# Determine tfvars file path (always primary site)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TFVARS_FILE="${SCRIPT_DIR}/tf-vars/${ENVIRONMENT}/${CLUSTER}.tfvars.json"

print_info "Migrating cluster state for PRIMARY site: ${WORKSPACE_NAME}"
print_info "Terraform vars file: ${TFVARS_FILE}"
print_info "This will remove old 'production' cluster from state and promote 'migration' to 'production'"
print_info "Requires cluster_count = 2 (both clusters must exist)"

# Check current workspace
CURRENT_WORKSPACE=$(terraform workspace show 2>/dev/null || echo "")
if [ "$CURRENT_WORKSPACE" != "$WORKSPACE_NAME" ]; then
    print_warning "Current workspace is '$CURRENT_WORKSPACE', switching to '$WORKSPACE_NAME'"
    terraform workspace select "$WORKSPACE_NAME" || {
        print_error "Failed to switch workspace. Please run 'terraform workspace select $WORKSPACE_NAME' first"
        exit 1
    }
fi

print_info "Current workspace: $(terraform workspace show)"

# Check if migration resources exist in state
print_info "Checking for migration resources in state..."

MIGRATION_CLUSTER_EXISTS=false
MIGRATION_SUFFIX_EXISTS=false

if terraform state list | grep -q 'module.dataproc_cluster\["migration"\]'; then
    MIGRATION_CLUSTER_EXISTS=true
    print_info "Found: module.dataproc_cluster[\"migration\"]"
fi

if terraform state list | grep -q 'random_id.dpc_cluster_suffix\["migration"\]'; then
    MIGRATION_SUFFIX_EXISTS=true
    print_info "Found: random_id.dpc_cluster_suffix[\"migration\"]"
fi

# Check if production resources exist
PRODUCTION_CLUSTER_EXISTS=false
PRODUCTION_SUFFIX_EXISTS=false

if terraform state list | grep -q 'module.dataproc_cluster\["production"\]'; then
    PRODUCTION_CLUSTER_EXISTS=true
    print_warning "Found: module.dataproc_cluster[\"production\"] (will be replaced)"
fi

if terraform state list | grep -q 'random_id.dpc_cluster_suffix\["production"\]'; then
    PRODUCTION_SUFFIX_EXISTS=true
    print_warning "Found: random_id.dpc_cluster_suffix[\"production\"] (will be replaced)"
fi

if [ "$MIGRATION_CLUSTER_EXISTS" = false ] && [ "$MIGRATION_SUFFIX_EXISTS" = false ]; then
    print_error "No migration resources found in state."
    print_error "Migration cluster may not exist or migration has already been completed."
    exit 1
fi

# Check if tfvars file exists
if [ ! -f "$TFVARS_FILE" ]; then
    print_error "Terraform vars file not found: ${TFVARS_FILE}"
    exit 1
fi

# Check for JSON manipulation tool
if command -v jq &> /dev/null; then
    JSON_TOOL="jq"
elif command -v python3 &> /dev/null; then
    JSON_TOOL="python3"
else
    print_error "Neither 'jq' nor 'python3' found. Please install one to update JSON files."
    exit 1
fi

# Check current cluster_count in tfvars - must be 1 to run this script
CURRENT_COUNT=""
if [ "$JSON_TOOL" = "jq" ]; then
    CURRENT_COUNT=$(jq -r '.dataproc_cluster.cluster_count // empty' "$TFVARS_FILE" 2>/dev/null || echo "")
else
    CURRENT_COUNT=$(python3 -c "import json, sys; data = json.load(open('$TFVARS_FILE')); print(data.get('dataproc_cluster', {}).get('cluster_count', ''))" 2>/dev/null || echo "")
fi

# The script should only run when cluster_count is 2 (during migration)
# After running, it will update cluster_count to 1
if [ -z "$CURRENT_COUNT" ]; then
    print_error "Could not determine cluster_count from tfvars file"
    print_error "Please ensure 'dataproc_cluster.cluster_count' exists in ${TFVARS_FILE}"
    exit 1
fi

if [ "$CURRENT_COUNT" != "2" ]; then
    print_error "This script should only run when cluster_count is 2 (during migration)"
    print_error "Current cluster_count in ${TFVARS_FILE} is: ${CURRENT_COUNT}"
    print_error ""
    print_info "Workflow:"
    echo "  1. Start migration: set cluster_count to 2 (creates both clusters)"
    echo "  2. Migrate data from production (cluster-1) to migration (cluster-0)"
    echo "  3. Run this script to remove old production and promote migration to production"
    echo "  4. Run terraform apply to complete the migration"
    exit 1
fi

print_success "Cluster count verified: ${CURRENT_COUNT} (migration in progress)"

# Confirm before proceeding
echo ""
print_warning "This operation will:"
if [ "$PRODUCTION_CLUSTER_EXISTS" = true ]; then
    echo "  - REMOVE module.dataproc_cluster[\"production\"] from Terraform state (old cluster)"
fi
if [ "$PRODUCTION_SUFFIX_EXISTS" = true ]; then
    echo "  - REMOVE random_id.dpc_cluster_suffix[\"production\"] from Terraform state (old suffix)"
fi
if [ "$MIGRATION_CLUSTER_EXISTS" = true ]; then
    echo "  - Move module.dataproc_cluster[\"migration\"] → module.dataproc_cluster[\"production\"]"
fi
if [ "$MIGRATION_SUFFIX_EXISTS" = true ]; then
    echo "  - Move random_id.dpc_cluster_suffix[\"migration\"] → random_id.dpc_cluster_suffix[\"production\"]"
fi
echo "  - Update ${TFVARS_FILE}: set \"cluster_count\" from 2 to 1"
echo ""
print_warning "After this, run 'terraform apply' to delete the old production cluster"
echo ""

read -p "Do you want to proceed? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_info "Operation cancelled."
    exit 0
fi

# Perform state operations
OPERATION_SUCCESS=true

# Step 1: Remove old production resources from state
OLD_PRODUCTION_CLUSTER_NAME=""
if [ "$PRODUCTION_CLUSTER_EXISTS" = true ]; then
    # Extract the cluster name before removing it from state
    print_info "Extracting old production cluster name from state..."
    STATE_OUTPUT=$(terraform state show 'module.dataproc_cluster["production"]' 2>/dev/null || echo "")
    if [ -n "$STATE_OUTPUT" ]; then
        # Extract name from terraform state show output
        OLD_PRODUCTION_CLUSTER_NAME=$(echo "$STATE_OUTPUT" | grep -E '^\s+name\s+=' | head -1 | sed 's/.*= *"\(.*\)"/\1/' | tr -d ' ')
        if [ -n "$OLD_PRODUCTION_CLUSTER_NAME" ]; then
            print_info "Old production cluster name: ${OLD_PRODUCTION_CLUSTER_NAME}"
            print_warning "This cluster will be deleted when you run 'terraform apply'"
        fi
    fi
    
    print_info "Removing module.dataproc_cluster[\"production\"] from Terraform state..."
    if terraform state rm 'module.dataproc_cluster["production"]' 2>/dev/null; then
        print_success "Successfully removed old production cluster from state"
        if [ -n "$OLD_PRODUCTION_CLUSTER_NAME" ]; then
            echo "  → Cluster name removed: ${OLD_PRODUCTION_CLUSTER_NAME}"
        fi
    else
        print_error "Failed to remove old production cluster from state"
        OPERATION_SUCCESS=false
    fi
fi

if [ "$PRODUCTION_SUFFIX_EXISTS" = true ]; then
    print_info "Removing random_id.dpc_cluster_suffix[\"production\"] from Terraform state..."
    if terraform state rm 'random_id.dpc_cluster_suffix["production"]' 2>/dev/null; then
        print_success "Successfully removed old production suffix from state"
    else
        print_error "Failed to remove old production suffix from state"
        OPERATION_SUCCESS=false
    fi
fi

# Step 2: Move migration resources to production
if [ "$MIGRATION_CLUSTER_EXISTS" = true ]; then
    print_info "Moving module.dataproc_cluster[\"migration\"] to module.dataproc_cluster[\"production\"]..."
    if terraform state mv 'module.dataproc_cluster["migration"]' 'module.dataproc_cluster["production"]' 2>/dev/null; then
        print_success "Successfully moved migration cluster to production"
    else
        print_error "Failed to move migration cluster to production"
        OPERATION_SUCCESS=false
    fi
fi

if [ "$MIGRATION_SUFFIX_EXISTS" = true ]; then
    print_info "Moving random_id.dpc_cluster_suffix[\"migration\"] to random_id.dpc_cluster_suffix[\"production\"]..."
    if terraform state mv 'random_id.dpc_cluster_suffix["migration"]' 'random_id.dpc_cluster_suffix["production"]' 2>/dev/null; then
        print_success "Successfully moved migration suffix to production"
    else
        print_error "Failed to move migration suffix to production"
        OPERATION_SUCCESS=false
    fi
fi

echo ""
if [ "$OPERATION_SUCCESS" = true ]; then
    print_success "Cluster state migration completed successfully!"
    
    # Update tfvars file: change cluster_count from 2 to 1
    print_info "Updating tfvars file: ${TFVARS_FILE} (cluster_count: 2 → 1)"
    if [ "$JSON_TOOL" = "jq" ]; then
        # Use jq to update cluster_count
        TMP_FILE=$(mktemp)
        jq '.dataproc_cluster.cluster_count = 1' "$TFVARS_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$TFVARS_FILE"
        if [ $? -eq 0 ]; then
            print_success "Successfully updated cluster_count to 1 in tfvars file"
        else
            print_warning "Failed to update tfvars file automatically. Please manually set 'cluster_count': 1"
        fi
    else
        # Use python3 to update cluster_count
        python3 << EOF
import json
import sys

try:
    with open('${TFVARS_FILE}', 'r') as f:
        data = json.load(f)
    
    if 'dataproc_cluster' in data:
        data['dataproc_cluster']['cluster_count'] = 1
    
    with open('${TFVARS_FILE}', 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    
    print("Successfully updated cluster_count to 1")
    sys.exit(0)
except Exception as e:
    print(f"Error updating tfvars: {e}")
    sys.exit(1)
EOF
        if [ $? -eq 0 ]; then
            print_success "Successfully updated cluster_count to 1 in tfvars file"
        else
            print_warning "Failed to update tfvars file automatically. Please manually set 'cluster_count': 1"
        fi
    fi
    
    print_info "Summary of changes:"
    echo "  ✓ Old production cluster removed from Terraform state"
    if [ -n "$OLD_PRODUCTION_CLUSTER_NAME" ]; then
        echo "    → Cluster to be deleted: ${OLD_PRODUCTION_CLUSTER_NAME}"
    fi
    echo "  ✓ Migration cluster promoted to production"
    echo "  ✓ cluster_count updated from 2 to 1"
    echo ""
    print_info "Next steps:"
    if [ "$AUTO_APPLY" = true ]; then
        echo "  1. Reviewing updated tfvars file..."
        echo "  2. Running terraform plan..."
        terraform plan -var-file="$TFVARS_FILE" || {
            print_error "Terraform plan failed. Please review the errors above."
            exit 1
        }
        echo ""
        if [ -n "$OLD_PRODUCTION_CLUSTER_NAME" ]; then
            print_warning "This will DELETE the old production cluster: ${OLD_PRODUCTION_CLUSTER_NAME}"
        else
            print_warning "This will DELETE the old production cluster (now removed from state)"
        fi
        read -p "Do you want to apply these changes? (yes/no): " APPLY_CONFIRM
        if [ "$APPLY_CONFIRM" = "yes" ]; then
            print_info "Running terraform apply..."
            terraform apply -var-file="$TFVARS_FILE" || {
                print_error "Terraform apply failed. Please review the errors above."
                exit 1
            }
            print_success "Migration completed! The old production cluster has been deleted."
        else
            print_info "Apply cancelled. You can run 'terraform apply -var-file=\"${TFVARS_FILE}\"' later."
        fi
    else
        echo "  1. Review the updated tfvars file: ${TFVARS_FILE}"
        echo "  2. Run: terraform plan -var-file=\"${TFVARS_FILE}\""
        echo "  3. Verify the plan shows deletion of the old production cluster (removed from state)"
        echo "  4. Run: terraform apply -var-file=\"${TFVARS_FILE}\" to delete the old cluster"
        echo ""
        if [ -n "$OLD_PRODUCTION_CLUSTER_NAME" ]; then
            print_warning "Important: terraform apply will DELETE the old production cluster: ${OLD_PRODUCTION_CLUSTER_NAME}"
        else
            print_warning "Important: terraform apply will DELETE the old production cluster"
        fi
        echo ""
        print_info "Tip: Use --auto-apply flag to automatically run terraform apply after migration"
    fi
else
    print_error "Some state operations failed. Please check the errors above."
    print_error "You may need to manually complete the state migration."
    exit 1
fi
