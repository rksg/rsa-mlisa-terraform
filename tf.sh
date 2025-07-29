#!/bin/bash

# Terraform Wrapper Script
# This script provides a simplified interface for the Terraform wrapper

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

# Function to show usage
show_usage() {
    cat << EOF
Terraform Wrapper Script

Usage: $0 <environment> <cluster> <action> [options]

Arguments:
  environment    Environment to deploy to (stg, prod-us, prod-eu, prod-asia)
  cluster        Cluster type (rai, r1-rai)
  action         Terraform action (init, plan, apply, destroy, output, show)

Options:
  --target-site <site>    Target site (primary, dr) [default: primary]
  --get-gcp-resources-site <site>     Get GCP resources from site (primary, dr, none) to generate tfvars file [default: none]
  --auto-approve          Auto-approve changes (for apply and destroy)
  --force                 Force reinitialization (for init)
  --detailed              Show detailed output (for plan)

Examples:
  $0 stg r1-rai init
  $0 prod-us rai plan
  $0 stg r1-rai init --get-gcp-resources-site primary --target-site dr
  $0 prod-eu r1-rai apply --auto-approve
  $0 stg rai destroy
  $0 prod-asia r1-rai show

EOF
}

# Function to validate arguments
validate_args() {
    local environment=$1
    local cluster=$2
    local action=$3
    local target_site=$4    
    local get_gcp_resources_site=$5
    
    # Validate environment
    case $environment in
        stg|prod-us|prod-eu|prod-asia)
            ;;
        *)
            print_error "Invalid environment: $environment"
            print_info "Valid environments: stg, prod-us, prod-eu, prod-asia"
            exit 1
            ;;
    esac
    
    # Validate cluster
    case $cluster in
        rai|r1-rai)
            ;;
        *)
            print_error "Invalid cluster: $cluster"
            print_info "Valid clusters: rai, r1-rai"
            exit 1
            ;;
    esac
    
    # Validate action
    case $action in
        init|plan|apply|destroy|output|show)
            ;;
        *)
            print_error "Invalid action: $action"
            print_info "Valid actions: init, plan, apply, destroy, output, show"
            exit 1
            ;;
    esac

    # Validate target site
    case $target_site in
        primary|dr)
            ;;
        *)
            print_error "Invalid target site: $target_site"
            print_info "Valid target sites: primary, dr"
            exit 1
            ;;
    esac

    # Validate get gcp resources
    case $get_gcp_resources_site in
        primary|dr|none)
            ;;
        *)
            print_error "Invalid get gcp resources: $get_gcp_resources_site"
            print_info "Valid get gcp resources site: primary, dr, none"
            exit 1
            ;;
    esac
}

# Function to check if Python script exists
check_python_script() {
    if [[ ! -f "terraform_wrapper.py" ]]; then
        print_error "terraform_wrapper.py not found in current directory"
        exit 1
    fi
}

# Function to check if Terraform is installed
check_terraform() {
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed or not in PATH"
        print_info "Please install Terraform and try again"
        exit 1
    fi
}

# Function to show confirmation for destructive actions
confirm_destructive_action() {
    local action=$1
    local environment=$2
    local cluster=$3
    
    if [[ $action == "apply" || $action == "destroy" ]]; then
        print_warning "This will perform: $action"
        print_warning "Environment: $environment"
        print_warning "Cluster: $cluster"
        echo
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Operation cancelled"
            exit 0
        fi
    fi
}

# Main script
main() {
    # Check if help is requested
    if [[ $1 == "-h" || $1 == "--help" ]]; then
        show_usage
        exit 0
    fi
    
    # Check if we have enough arguments
    if [[ $# -lt 3 ]]; then
        print_error "Insufficient arguments"
        show_usage
        exit 1
    fi
    
    # Parse arguments
    local environment=$1
    local cluster=$2
    local action=$3
    shift 3
    
    # Parse options
    local target_site="primary"
    local get_gcp_resources_site="none"
    local auto_approve=""
    local force=""
    local detailed=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --target-site)
                target_site=$2
                shift 2
                ;;
            --get-gcp-resources-site)
                get_gcp_resources_site=$2
                shift 2
                ;;
            --auto-approve)
                auto_approve="--auto-approve"
                shift
                ;;
            --force)
                force="--force"
                shift
                ;;
            --detailed)
                detailed="--detailed"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate arguments
    validate_args "$environment" "$cluster" "$action" "$target_site" "$get_gcp_resources_site"
    
    # Check prerequisites
    check_python_script
    check_terraform
    
    # Show confirmation for destructive actions
    confirm_destructive_action "$action" "$environment" "$cluster"
    
    # Build command
    local cmd="python3 terraform_wrapper.py"
    cmd="$cmd --environment $environment"
    cmd="$cmd --cluster $cluster"
    cmd="$cmd --target-site $target_site"
    cmd="$cmd --action $action"
    cmd="$cmd --get-gcp-resources-site $get_gcp_resources_site"
    
    if [[ -n $auto_approve ]]; then
        cmd="$cmd $auto_approve"
    fi
    
    if [[ -n $force ]]; then
        cmd="$cmd $force"
    fi
    
    if [[ -n $detailed ]]; then
        cmd="$cmd $detailed"
    fi
    
    # Execute command
    print_info "Executing: $cmd"
    echo
    
    if eval $cmd; then
        print_success "Operation completed successfully"
    else
        print_error "Operation failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 