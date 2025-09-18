# RSA MLISA Terraform Infrastructure

A comprehensive Terraform-based infrastructure management system for RSA MLISA (Machine Learning Infrastructure for Security Analytics) with full disaster recovery (DR) support, automated GCP resource discovery, and Kubernetes deployment capabilities.

## 🏗️ Architecture Overview

This project provides a complete infrastructure-as-code solution for deploying and managing MLISA workloads across multiple environments with the following key components:

### Core Infrastructure Components
- **Terraform Modules**: Modular infrastructure components for GCP resources
- **Python Wrapper**: Automated workspace management and resource discovery
- **Kubernetes Integration**: Automated deployment of MLISA workloads
- **Disaster Recovery**: Complete primary/DR site support
- **Multi-Environment**: Support for staging and production environments

### Supported GCP Resources
- **Networking**: VPC, Subnets, NAT Gateways, VPC Connectors, Firewall Rules
- **Compute**: DataProc Clusters, GKE Clusters, Compute Addresses
- **Serverless**: Cloud Functions, Cloud Run Services
- **Data & Storage**: Redis Instances, Cloud SQL PostgreSQL
- **Security**: Firewall rules with intelligent IP range management

## 🚀 Key Features

- **Automated Workspace Management**: Creates and manages environment-specific Terraform workspaces
- **Multi-Environment Support**: Staging, production US, EU, and Asia environments
- **Cluster Management**: Support for different cluster types (rai, r1-rai)
- **Comprehensive Disaster Recovery**: Full primary/DR site support across all GCP resource types
- **Intelligent Resource Discovery**: Automatic discovery and configuration of GCP resources
- **Smart Firewall Management**: Intelligent source range handling based on firewall rule types
- **Kubernetes Integration**: Automated deployment with string replacement capabilities
- **Interactive Mode**: User confirmation for destructive operations
- **Comprehensive Logging**: Detailed output and error handling
- **Zero Dependencies**: Uses only Python standard library and gcloud CLI
- **Advanced IP Range Management**: Site-specific IP range configuration

## 📁 Project Structure

```
rsa-mlisa-terraform/
├── main.tf                          # Main Terraform configuration
├── variables.tf                     # Global variable definitions
├── output.tf                        # Global outputs
├── providers.tf                     # Terraform provider configuration
├── terraform_wrapper.py             # Python wrapper for Terraform operations
├── apply_resources.py               # Kubernetes resource deployment script
├── tf.sh                           # Shell wrapper script
├── modules/                         # Terraform modules
│   ├── cloud_function/              # Cloud Functions module
│   ├── cloud_run/                   # Cloud Run services module
│   ├── compute_address/             # Compute addresses module
│   ├── container_cluster/           # GKE clusters module
│   ├── dataproc/                    # DataProc clusters module
│   ├── firewall/                    # Firewall rules module
│   ├── nat/                         # NAT gateways module
│   ├── redis/                       # Redis instances module
│   ├── sql_postgres/                # Cloud SQL PostgreSQL module
│   ├── subnetwork/                  # VPC subnets module
│   └── vpc_connect/                 # VPC connectors module
├── tf-vars/                         # Environment-specific variables
│   └── stg/                         # Staging environment
│       ├── rai.tfvars.json          # Primary site configuration
│       ├── rai-dr.tfvars.json       # DR site configuration
│       ├── r1-rai.tfvars.json       # R1-RAI primary configuration
│       └── r1-rai-dr.tfvars.json    # R1-RAI DR configuration
├── kube-resources/                  # Kubernetes resource definitions
│   └── stg/                         # Staging K8s resources
│       ├── rai-druid-resources.yaml # Druid deployment manifests
│       ├── r1-rai-druid-resources.yaml # R1-RAI Druid manifests
│       └── rai-kafka-resources.yaml # Kafka deployment manifests
└── terraform.tfstate.d/             # Terraform state files
    ├── stg-rai-primary/             # Primary site state
    ├── stg-rai-dr/                  # DR site state
    ├── stg-r1-rai-primary/          # R1-RAI primary state
    └── stg-r1-rai-dr/               # R1-RAI DR state
```

## 🛠️ Terraform Modules

### Networking Modules
- **`subnetwork/`**: Manages VPC subnets with secondary IP ranges for GKE
- **`nat/`**: Configures NAT gateways for outbound internet access
- **`vpc_connect/`**: Creates VPC connectors for serverless services
- **`firewall/`**: Manages firewall rules with intelligent IP range handling

### Compute Modules
- **`dataproc/`**: Deploys DataProc clusters for big data processing
- **`container_cluster/`**: Creates GKE clusters with node pools
- **`compute_address/`**: Manages static IP addresses

### Serverless Modules
- **`cloud_function/`**: Deploys Cloud Functions with VPC connectivity
- **`cloud_run/`**: Manages Cloud Run services

### Data & Storage Modules
- **`redis/`**: Creates Redis instances for caching
- **`sql_postgres/`**: Deploys Cloud SQL PostgreSQL instances

## Prerequisites

- **Python 3.7+** (standard library only - no external packages required)
- **Terraform >= 1.10** installed and in PATH
- **Google Cloud SDK (gcloud)** configured and authenticated
- **kubectl** for Kubernetes deployments
- **Appropriate GCP project access** with required permissions

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rsa-mlisa-terraform
   ```

2. **Make scripts executable**:
   ```bash
   chmod +x tf.sh
   chmod +x terraform_wrapper.py
   chmod +x apply_resources.py
   ```

3. **Configure GCP authentication**:
   ```bash
   gcloud auth login
   gcloud config set project <your-project-id>
   ```

4. **Set up environment variables** (for PostgreSQL passwords):
   ```bash
   export TF_VAR_sql_postgres_password='{"druid": "your-druid-password", "mlisa": "your-mlisa-password"}'
   ```

## Configuration

The system uses environment-specific tfvars files located in `tf-vars/{environment}/` directory. Each environment contains:

- **Primary site configuration**: `{cluster}.tfvars.json`
- **DR site configuration**: `{cluster}-dr.tfvars.json`

## 🚀 Usage

### Shell Wrapper (Recommended)

The `tf.sh` script provides a simplified interface for common operations:

```bash
# Basic Terraform operations
./tf.sh <environment> <cluster> <action> [options]

# Examples:
./tf.sh stg r1-rai init                    # Initialize staging R1-RAI
./tf.sh prod-us rai plan                   # Plan production US RAI
./tf.sh prod-eu r1-rai apply --auto-approve # Apply with auto-approve
./tf.sh stg rai destroy                    # Destroy staging RAI

# DR site operations
./tf.sh stg r1-rai plan --target-site dr   # Plan DR site
./tf.sh prod-us rai apply --target-site dr # Apply to DR site

# Advanced options
./tf.sh stg rai plan --detailed            # Detailed plan output
./tf.sh stg r1-rai init --force           # Force reinitialization
./tf.sh stg rai apply --auto-approve       # Skip confirmation prompts

# GCS integration
./tf.sh stg rai plan --skip-vars-from-gcs  # Skip GCS variable sync
./tf.sh stg rai plan --gcs-bucket-name my-bucket # Custom GCS bucket

# Get replacement values for Kubernetes
./tf.sh stg rai get_replacement_values --target-site dr
```

### Python Script (Advanced)

For advanced usage and automation, use the Python script directly:

```bash
# Basic operations
python3 terraform_wrapper.py --environment stg --cluster r1-rai --action init
python3 terraform_wrapper.py --environment prod-us --cluster rai --action plan
python3 terraform_wrapper.py --environment prod-eu --cluster r1-rai --action apply --auto-approve

# DR site operations
python3 terraform_wrapper.py --environment stg --cluster rai --action plan --target-site dr

# Advanced options
python3 terraform_wrapper.py --environment stg --cluster r1-rai --action init --force
python3 terraform_wrapper.py --environment prod-us --cluster rai --action plan --detailed

# Get replacement values
python3 terraform_wrapper.py --environment stg --cluster rai --action get_replacement_values --target-site dr
```

### Kubernetes Deployment

Use `apply_resources.py` to deploy Kubernetes resources with string replacements:

```bash
# Basic deployment with JSON string
python3 apply_resources.py -f kube-resources/stg/rai-druid-resources.yaml -r '{"postgresql_druid_host" : "10.216.116.45"}'

# With specific Kubernetes context
python3 apply_resources.py -f kube-resources/stg/rai-kafka-resources.yaml -r '{"postgresql_druid_host" : "10.216.116.45"}' -c production

# Dry run mode
python3 apply_resources.py -f kube-resources/stg/rai-druid-resources.yaml -r '{"postgresql_druid_host" : "10.216.116.45"}' --dry-run
```

## 📋 Available Actions

| Action | Description | Use Case |
|--------|-------------|----------|
| `init` | Initialize Terraform workspace | First-time setup, after code changes |
| `plan` | Show planned changes | Review changes before applying |
| `apply` | Apply changes to infrastructure | Deploy infrastructure changes |
| `destroy` | Destroy infrastructure | Clean up resources |
| `output` | Show Terraform outputs | Get resource information |
| `show` | Show current state | Inspect current infrastructure |
| `get_replacement_values` | Get values for K8s replacements | Generate K8s deployment values |

## ⚙️ Options

| Option | Description | Applicable Actions | Default |
|--------|-------------|-------------------|---------|
| `--target-site` | Target site (primary/dr) | All | primary |
| `--auto-approve` | Skip confirmation prompts | apply, destroy | false |
| `--force` | Force reinitialization | init | false |
| `--detailed` | Show detailed exit codes | plan | false |
| `--skip-vars-from-gcs` | Skip GCS variable sync | All | false |
| `--gcs-bucket-name` | Custom GCS bucket name | All | mlisa-dr-resource-backup |

## 🔄 Complete Workflow

### 1. Infrastructure Deployment

```bash
# Step 1: Initialize Terraform workspace
./tf.sh stg rai init

# Step 2: Plan changes
./tf.sh stg rai plan

# Step 3: Apply infrastructure
./tf.sh stg rai apply

# Step 4: Get replacement values for Kubernetes
./tf.sh stg rai get_replacement_values --target-site dr
```

### 2. Disaster Recovery Setup

```bash
# Step 1: Deploy primary site
./tf.sh stg rai apply

# Step 2: Deploy DR site
./tf.sh stg rai apply --target-site dr

# Step 3: Verify both sites
./tf.sh stg rai output
```

### 3. Kubernetes Deployment

```bash
# Step 1: Get infrastructure values as JSON string
REPLACEMENTS=$(./tf.sh stg rai get_replacement_values --target-site dr)

# Step 2: Deploy Kubernetes resources
python3 apply_resources.py \
  -f kube-resources/stg/rai-druid-resources.yaml \
  -r "$REPLACEMENTS"

# Step 3: Deploy Kafka resources
python3 apply_resources.py \
  -f kube-resources/stg/rai-kafka-resources.yaml \
  -r "$REPLACEMENTS"
```

## 🏷️ Workspace Naming

Workspaces are automatically named using the pattern:
```
{environment}-{cluster}-{target_site}
```

**Examples:**
- `stg-r1-rai-primary` - Staging R1-RAI primary site
- `prod-us-rai-primary` - Production US RAI primary site  
- `prod-eu-r1-rai-dr` - Production EU R1-RAI DR site

## 🐍 Python Scripts Documentation

### terraform_wrapper.py

The main Python wrapper provides comprehensive Terraform workspace management and resource discovery capabilities.

#### Key Features
- **Automated Workspace Management**: Creates and switches between environment-specific workspaces
- **Resource Discovery**: Automatically discovers GCP resources and generates tfvars files
- **DR Support**: Full primary/DR site configuration generation
- **Error Handling**: Comprehensive error handling and logging
- **JSON Output**: Uses `terraform output -json` for reliable data parsing

#### Core Classes

**`TerraformAction` (Enum)**
- Defines available Terraform operations: `INIT`, `PLAN`, `APPLY`, `DESTROY`, `OUTPUT`, `SHOW`, `GET_REPLACEMENT_VALUES`

**`TerraformWrapper` (Class)**
- Main wrapper class for managing Terraform operations
- Handles workspace creation, switching, and command execution
- Provides resource discovery and replacement value generation

#### Key Methods

- **`_run_terraform_get_replacement_values()`**: Generates replacement values for Kubernetes deployments
- **`_create_or_switch_workspace()`**: Manages Terraform workspace lifecycle
- **`execute_action()`**: Main entry point for executing Terraform actions

### apply_resources.py

Python script for deploying Kubernetes resources with string replacements.

#### Key Features
- **String Replacements**: Applies multiple string replacements to YAML files
- **JSON String Input**: Accepts replacement configurations as JSON strings
- **YAML Cleaning**: Automatically removes trailing `%` characters
- **Kubernetes Integration**: Uses kubectl for resource deployment
- **Dry Run Support**: Test changes without applying them
- **Error Handling**: Comprehensive error handling and cleanup

#### Usage Examples

```bash
# Basic deployment with JSON string
python3 apply_resources.py -f resources.yaml -r ''{"postgresql_druid_host" : "10.216.116.45"}''

# With context and dry run
python3 apply_resources.py -f resources.yaml -r ''{"postgresql_druid_host" : "10.216.116.45"}'' -c production --dry-run
```

## 🔧 Environment Variables

The system uses the following environment variables:

### Required Environment Variables
```bash
# PostgreSQL database passwords (JSON format)
export TF_VAR_sql_postgres_password='{"druid": "your-druid-password", "mlisa": "your-mlisa-password"}'
```

### Automatically Set Variables
The wrapper automatically sets these variables for Terraform:
- `TF_VAR_project_id`: GCP project ID
- `TF_VAR_region`: GCP region  
- `TF_VAR_environment`: Environment name
- `TF_VAR_cluster`: Cluster type
- `TF_VAR_target_site`: Target site (primary/dr)

## 🛡️ Error Handling

The system includes comprehensive error handling:

- **Validation**: Checks for valid environments, clusters, and configurations
- **Prerequisites**: Verifies Terraform, kubectl, and gcloud installation
- **Workspace Management**: Handles workspace creation and switching errors
- **User Confirmation**: Prompts for destructive operations
- **JSON Parsing**: Robust error handling for Terraform output parsing
- **Resource Discovery**: Comprehensive error handling for GCP operations
- **Kubernetes Deployment**: Error handling for kubectl operations

## 📚 Comprehensive Examples

### 1. Complete MLISA Deployment

```bash
# Step 1: Deploy primary infrastructure
./tf.sh stg rai init
./tf.sh stg rai plan
./tf.sh stg rai apply

# Step 2: Deploy DR infrastructure  
./tf.sh stg rai init --target-site dr
./tf.sh stg rai plan --target-site dr
./tf.sh stg rai apply --target-site dr

# Step 3: Get replacement values as JSON string
REPLACEMENTS=$(./tf.sh stg rai get_replacement_values --target-site dr)

# Step 4: Deploy Kubernetes workloads
python3 apply_resources.py -f kube-resources/stg/rai-druid-resources.yaml -r "$REPLACEMENTS"
python3 apply_resources.py -f kube-resources/stg/rai-kafka-resources.yaml -r "$REPLACEMENTS"
```

### 2. Production Deployment with Auto-approve

```bash
# Deploy production infrastructure
./tf.sh prod-us rai init
./tf.sh prod-us rai plan --detailed
./tf.sh prod-us rai apply --auto-approve

# Deploy DR site
./tf.sh prod-us rai apply --target-site dr --auto-approve
```

### 3. Multi-Environment Deployment

```bash
# Deploy to multiple environments
for env in stg prod-us prod-eu; do
  for cluster in rai r1-rai; do
    ./tf.sh $env $cluster init
    ./tf.sh $env $cluster plan
    ./tf.sh $env $cluster apply --auto-approve
  done
done
```

### 4. Infrastructure Updates

```bash
# Update existing infrastructure
./tf.sh stg rai plan --detailed
./tf.sh stg rai apply

# Force reinitialization if needed
./tf.sh stg rai init --force
```

### 5. Disaster Recovery Testing

```bash
# Test DR site deployment
./tf.sh stg rai plan --target-site dr
./tf.sh stg rai apply --target-site dr

# Verify DR site outputs
./tf.sh stg rai output --target-site dr
```

### 6. Cleanup Operations

```bash
# Destroy staging environment
./tf.sh stg rai destroy

# Destroy with auto-approve
./tf.sh stg r1-rai destroy --auto-approve

# Destroy DR site
./tf.sh stg rai destroy --target-site dr
```

### 7. Kubernetes Resource Management

```bash
# Deploy with specific context using JSON string
python3 apply_resources.py \
  -f kube-resources/stg/rai-druid-resources.yaml \
  -r '{"postgresql_druid_host" : "10.216.116.45"}' \
  -c production

# Dry run deployment
python3 apply_resources.py \
  -f kube-resources/stg/rai-kafka-resources.yaml \
  -r '{"postgresql_druid_host" : "10.216.116.45"}' \
  --dry-run
```

## 🔧 Troubleshooting

### Common Issues

1. **Terraform not found**
   ```bash
   # Verify Terraform installation
   terraform --version
   # Install if needed: https://www.terraform.io/downloads
   ```

2. **GCP authentication issues**
   ```bash
   # Authenticate with GCP
   gcloud auth login
   gcloud config set project <your-project-id>
   # Verify access
   gcloud config get-value project
   ```

3. **kubectl not found**
   ```bash
   # Install kubectl
   # macOS: brew install kubectl
   # Linux: curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   ```

4. **JSON parsing errors**
   ```bash
   # The system now uses terraform output -json for reliable parsing
   # If you still see JSON errors, check your Terraform version
   terraform version
   ```

5. **Workspace creation fails**
   ```bash
   # Ensure write permissions
   ls -la terraform.tfstate.d/
   # Check for workspace conflicts
   terraform workspace list
   ```

6. **Permission denied errors**
   ```bash
   # Make scripts executable
   chmod +x tf.sh terraform_wrapper.py apply_resources.py
   ```

### Debug Mode

For detailed debugging, run commands with verbose output:

```bash
# Debug Terraform wrapper
python3 -v terraform_wrapper.py --environment stg --cluster rai --action plan

# Debug Kubernetes deployment
python3 apply_resources.py -f resources.yaml -r '{"postgresql_druid_host" : "10.216.116.45"}' --dry-run
```

### Validation Commands

```bash
# Check Terraform installation
terraform --version

# Check GCP authentication
gcloud auth list

# Check kubectl configuration
kubectl config current-context

# Verify Python dependencies
python3 -c "import yaml, json, subprocess; print('All dependencies available')"
```

## 🤝 Contributing

### Development Guidelines

1. **Code Style**: Follow Python PEP 8 guidelines
2. **Documentation**: Add comprehensive docstrings for all functions
3. **Error Handling**: Include robust error handling for all operations
4. **Testing**: Test with multiple environments and cluster types
5. **DR Support**: Ensure all new features support primary/DR configurations
6. **Naming**: Maintain consistent naming conventions for DR resources

### Adding New Terraform Modules

1. Create module directory in `modules/`
2. Include `main.tf`, `variables.tf`, and `output.tf`
3. Add module call to `main.tf`
4. Update variable definitions in `variables.tf`
5. Test with both primary and DR sites

### Adding New Python Features

1. Follow existing code patterns
2. Add comprehensive error handling
3. Include logging for debugging
4. Update documentation
5. Test with different environments

## 📋 Dependencies

### Required Tools
- **Python 3.7+** (standard library only)
- **Terraform >= 1.10**
- **Google Cloud SDK (gcloud)**
- **kubectl**
- **Git** (for version control)

### Python Dependencies
- **PyYAML** (for YAML processing in apply_resources.py)
- **Standard library modules**: `sys`, `subprocess`, `argparse`, `time`, `pathlib`, `typing`, `enum`, `json`, `os`, `tempfile`, `re`

## 🏆 Project Status

This project provides a complete infrastructure-as-code solution for RSA MLISA with:

- ✅ **Full GCP Resource Support**: All major GCP services covered
- ✅ **Disaster Recovery**: Complete primary/DR site support
- ✅ **Multi-Environment**: Staging and production environments
- ✅ **Kubernetes Integration**: Automated workload deployment
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Documentation**: Complete usage and troubleshooting guides

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the comprehensive examples
3. Check Terraform and GCP documentation
4. Verify all prerequisites are installed and configured

---

**RSA MLISA Terraform Infrastructure** - A comprehensive solution for managing MLISA workloads across multiple environments with full disaster recovery support. 