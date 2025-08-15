# Terraform Workspace Wrapper

A comprehensive Python wrapper for managing Terraform workspaces and operations across multiple environments and clusters with full disaster recovery (DR) support.

## Features

- **Workspace Management**: Automatically creates and switches to environment-specific Terraform workspaces
- **Multi-Environment Support**: Supports staging, production US, EU, and Asia environments
- **Cluster Management**: Handles different cluster types (rai, r1-rai)
- **Comprehensive Disaster Recovery**: Full primary/DR site support across ALL GCP resource types
- **Enhanced Resource Discovery**: Automatic discovery and configuration of GCP resources for both primary and DR sites considering Primary Site as source
- **Smart Firewall Management**: Intelligent source range handling based on firewall rule names and DR site requirements
- **Interactive Mode**: User confirmation for destructive operations
- **Comprehensive Logging**: Detailed output and error handling
- **Flexible Interface**: Both Python script and shell wrapper available
- **Zero Dependencies**: Uses only Python standard library and gcloud CLI - no external packages required
- **Advanced IP Range Management**: Site-specific IP range configuration for multi-site deployments

## Prerequisites

- Python 3.7+ (standard library only - no external packages required)
- Terraform installed and in PATH
- Google Cloud SDK (gcloud) configured and authenticated
- Appropriate GCP project access

## Installation

1. Clone the repository
2. Ensure Google Cloud SDK (gcloud) is installed and configured
3. Make the shell wrapper executable:
   ```bash
   chmod +x tf.sh
   ```

## Configuration

The wrapper uses configuration from `configs/config.json` with comprehensive IP range support:

```json
{
  "stg": {
    "project_id": "ops-alto-01",
    "region": "us-central1",
    "dr_region": "us-east1",
    "rai": {
      "vpc": "mlisa-sa",
      "ip_ranges": {
        "primary": {
          "subnet_ip_cidr_range": "10.1.1.0/28",
          "secondary_ip_range_pod": "10.2.2.0/24",
          "secondary_ip_range_svc": "10.3.3.0/24",
          "vpc_connector_ip_cidr_range": "10.4.4.0/28",
          "gke_master_ip_cidr_range": "10.5.5.0/28"
        },
        "dr": {
          "subnet_ip_cidr_range": "10.6.6.0/28",
          "secondary_ip_range_pod": "10.7.7.0/24",
          "secondary_ip_range_svc": "10.8.8.0/24",
          "vpc_connector_ip_cidr_range": "10.9.9.0/28",
          "gke_master_ip_cidr_range": "10.0.0.0/28"
        }
      }
    }
  }
}
```

## Usage

### Shell Wrapper (Recommended)

The shell wrapper provides a simplified interface:

```bash
# Initialize workspace
./tf.sh stg r1-rai init

# Plan changes
./tf.sh prod-us rai plan

# Apply changes with auto-approve
./tf.sh prod-eu r1-rai apply --auto-approve

# Destroy infrastructure
./tf.sh stg rai destroy

# Show current state
./tf.sh prod-asia r1-rai show

# Use DR site
./tf.sh stg r1-rai plan --target-site dr

# Refresh GCP resource variables by generating tfvars file for primary site
./tf.sh stg r1-rai plan --refresh-gcp-resource-vars --target-site dr

# Skip GCP resource generation (default behavior)
./tf.sh stg r1-rai plan --target-site dr
```

### Python Script

For more advanced usage, use the Python script directly:

```bash
# Initialize with force reconfiguration
python3 terraform_wrapper.py --environment stg --cluster r1-rai --action init --force

# Plan with detailed output
python3 terraform_wrapper.py --environment prod-us --cluster rai --action plan --detailed

# Apply with auto-approve
python3 terraform_wrapper.py --environment prod-eu --cluster r1-rai --action apply --auto-approve

# Destroy with confirmation
python3 terraform_wrapper.py --environment stg --cluster rai --action destroy
```

## Available Actions

| Action | Description |
|--------|-------------|
| `init` | Initialize Terraform workspace |
| `plan` | Show planned changes |
| `apply` | Apply changes to infrastructure |
| `destroy` | Destroy infrastructure |
| `output` | Show Terraform outputs |
| `show` | Show current state |

## Options

| Option | Description | Applicable Actions |
|--------|-------------|-------------------|
| `--target-site` | Target site (primary/dr) | All |
| `--refresh-gcp-resource-vars` | Refresh GCP resource variables by generating tfvars file for primary site | All |
| `--auto-approve` | Skip confirmation prompts | apply, destroy |
| `--force` | Force reinitialization | init |
| `--detailed` | Show detailed exit codes | plan |

## Workspace Naming

Workspaces are automatically named using the pattern:
```
{environment}-{cluster}-{target_site}
```

Examples:
- `stg-r1-rai-primary`
- `prod-us-rai-primary`
- `prod-eu-r1-rai-dr`

## GCP Resource Generation

The wrapper provides comprehensive GCP resource discovery and configuration generation for both primary and DR sites:

### **Enhanced Resource Discovery Features**

- **Automatic Resource Discovery**: Fetches compute networks, subnetworks, clusters, functions, and more
- **Dual Site Support**: Generates configurations for both primary and DR sites simultaneously considering Primary Site as source
- **Smart IP Range Management**: Automatically assigns site-specific IP ranges based on configuration
- **Gateway Address Calculation**: Intelligent gateway address calculation for subnetworks
- **Tfvars Generation**: Creates environment-specific `.tfvars.json` files for both sites
- **Configurable**: Can enable with `--refresh-gcp-resource-vars` flag to generate tfvars from primary site
- **Environment-Specific**: Generates separate files for each environment and cluster combination

### **Generated Resources with Full DR Support**

The wrapper discovers and documents the following GCP resources with comprehensive primary/DR configurations:

#### **Networking Resources**
- **Compute Networks**: VPC network configurations
- **Subnetworks**: Primary and DR subnetwork configurations with site-specific IP ranges
- **NAT Routers**: Primary and DR NAT router configurations with `-dr` naming
- **VPC Access Connectors**: VPC connector configurations for serverless services

#### **Compute Resources**
- **DataProc Clusters**: Primary and DR cluster configurations with DR subnetwork mappings
- **Container (GKE) Clusters**: Primary and DR GKE configurations with DR subnetwork and IP allocation policies
- **Compute Addresses**: Primary and DR static IP configurations with DR subnetwork mappings

#### **Serverless Resources**
- **Cloud Functions**: Primary and DR function configurations with DR VPC connector mappings
- **Cloud Run Services**: Primary and DR service configurations with DR VPC connector mappings

#### **Data & Storage Resources**
- **Redis Instances**: Primary and DR Redis configurations with DR network mappings
- **Cloud SQL PostgreSQL**: Primary and DR PostgreSQL configurations with DR private network mappings

#### **Security Resources**
- **Firewall Rules**: Primary and DR firewall rules with intelligent source range handling
  - **Smart Source Range Detection**: Automatically detects firewall rule types and applies appropriate IP ranges
  - **GKE-Specific Rules**: Handles `allow-gke` rules with pod and service IP ranges
  - **VM-Specific Rules**: Handles `allow-vms` rules with subnet IP ranges
  - **DR Site Support**: Applies DR IP ranges for DR firewall rules

### **DR Configuration Features**

#### **Naming Conventions**
- **Resource Names**: All DR resources automatically get `-dr` suffix
- **Network References**: DR subnetworks and networks get `-dr` suffix
- **VPC Connectors**: DR VPC connectors get `-dr` suffix

#### **IP Range Management**
- **Primary Site**: Uses primary IP ranges from configuration
- **DR Site**: Uses DR IP ranges from configuration
- **Automatic Mapping**: Seamlessly maps resources to appropriate IP ranges

#### **Configuration Preservation**
- **All Properties**: All resource properties preserved identically between primary and DR
- **No Data Loss**: Complete configuration maintained for both sites
- **DR-Specific Changes**: Only names and network references get DR-specific modifications

### **Output Files**

The wrapper generates two comprehensive configuration files:

1. **Primary Configuration**: `{cluster}.tfvars.json` - Contains all resources for primary site
2. **DR Configuration**: `{cluster}-dr.tfvars.json` - Contains all resources for DR site with `-dr` suffixes

## Environment Variables

The wrapper automatically sets the following environment variables for Terraform:

- `TF_VAR_project_id`: GCP project ID
- `TF_VAR_region`: GCP region
- `TF_VAR_environment`: Environment name
- `TF_VAR_cluster`: Cluster type
- `TF_VAR_target_site`: Target site (primary/dr)

## Error Handling

The wrapper includes comprehensive error handling:

- **Validation**: Checks for valid environments, clusters, and configurations
- **Prerequisites**: Verifies Terraform installation and script availability
- **Workspace Management**: Handles workspace creation and switching errors
- **User Confirmation**: Prompts for destructive operations
- **Detailed Output**: Provides clear success/failure messages
- **Resource Discovery**: Comprehensive error handling for GCP resource discovery operations

## Examples

### Basic Workflow

```bash
# 1. Initialize workspace
./tf.sh stg r1-rai init

# 2. Plan changes
./tf.sh stg r1-rai plan

# 3. Apply changes
./tf.sh stg r1-rai apply

# 4. Check outputs
./tf.sh stg r1-rai output
```

### Production Deployment

```bash
# Plan production changes
./tf.sh prod-us rai plan --detailed

# Apply with auto-approve (use with caution)
./tf.sh prod-us rai apply --auto-approve
```

### Disaster Recovery

```bash
# Plan DR deployment
./tf.sh prod-eu r1-rai plan --target-site dr

# Apply DR changes
./tf.sh prod-eu r1-rai apply --target-site dr
```

### GCP Resource Management

```bash
# Refresh GCP resource variables by generating tfvars file for primary site
./tf.sh stg r1-rai plan --refresh-gcp-resource-vars --target-site dr

# Skip GCP resource generation (default behavior) for faster execution
./tf.sh stg r1-rai plan --target-site dr

# Refresh resources for production environment
./tf.sh prod-us rai plan --refresh-gcp-resource-vars
```

### Cleanup

```bash
# Destroy staging environment
./tf.sh stg rai destroy

# Destroy with auto-approve
./tf.sh stg r1-rai destroy --auto-approve
```

## Troubleshooting

### Common Issues

1. **Terraform not found**
   - Ensure Terraform is installed and in PATH
   - Run `terraform --version` to verify

2. **Configuration file not found**
   - Check that `configs/config.json` exists
   - Verify file permissions

3. **Workspace creation fails**
   - Ensure you have write permissions in the current directory
   - Check if workspace name conflicts exist

4. **GCP authentication issues**
   - Run `gcloud auth login` to authenticate
   - Verify project access with `gcloud config get-value project`

5. **Resource discovery failures**
   - Ensure gcloud CLI is properly configured
   - Verify network and subnetwork access permissions
   - Check IP range configuration in config.json

### Debug Mode

For debugging, run the Python script directly with verbose output:

```bash
python3 -v terraform_wrapper.py --environment stg --cluster r1-rai --action plan
```

### Resource Discovery Debugging

To debug GCP resource discovery issues:

```bash
# Test resource discovery directly
python3 gcp_resource_reader.py --environment stg --cluster rai

# Check generated tfvars files
ls -la configs/stg/
cat configs/stg/rai.tfvars.json
cat configs/stg/rai-dr.tfvars.json
```

## Contributing

1. Follow Python PEP 8 style guidelines
2. Add comprehensive docstrings for new functions
3. Include error handling for all external operations
4. Test with multiple environments and clusters
5. Ensure all new resource types support primary/DR configurations
6. Maintain consistent naming conventions for DR resources

## License

This project is licensed under the MIT License. 