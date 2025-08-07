# Terraform Workspace Wrapper

A comprehensive Python wrapper for managing Terraform workspaces and operations across multiple environments and clusters.

## Features

- **Workspace Management**: Automatically creates and switches to environment-specific Terraform workspaces
- **Multi-Environment Support**: Supports staging, production US, EU, and Asia environments
- **Cluster Management**: Handles different cluster types (rai, r1-rai)
- **Disaster Recovery**: Supports primary and DR site deployments
- **Interactive Mode**: User confirmation for destructive operations
- **Comprehensive Logging**: Detailed output and error handling
- **Flexible Interface**: Both Python script and shell wrapper available

## Prerequisites

- Python 3.7+
- Terraform installed and in PATH
- Google Cloud SDK (gcloud) configured
- Appropriate GCP project access

## Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make the shell wrapper executable:
   ```bash
   chmod +x tf.sh
   ```

## Configuration

The wrapper uses configuration from `configs/config.json`:

```json
{
  "stg": {
    "project_id": "ops-alto-01",
    "region": "us-central1",
    "dr_project_id": "ops-alto-01-dr",
    "dr_region": "us-central1",
    "rai": {
      "vpc": "mlisa-sa"
    },
    "r1-rai": {
      "vpc": "main"
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

# Get GCP resources from primary site to generate tfvars file
./tf.sh stg r1-rai plan --get-gcp-resources-site primary --target-site dr

# Skip GCP resource generation
./tf.sh stg r1-rai plan --get-gcp-resources-site none
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
| `--get-gcp-resources-site` | Get GCP resources from site (primary, dr, none) to generate tfvars file | All |
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

The wrapper can automatically fetch GCP resources and generate Terraform variables files:

- **Automatic Resource Discovery**: Fetches compute networks, subnetworks, clusters, functions, and more
- **Tfvars Generation**: Creates environment-specific `.tfvars.json` files
- **Configurable**: Can choose the site (primary/dr) and disable with `--get-gcp-resources-site` option
- **Environment-Specific**: Generates separate files for each environment and cluster combination

### Generated Resources

The wrapper discovers and documents the following GCP resources:
- Compute Networks and Subnetworks
- NAT Routers and VPC Access Connectors
- DataProc Clusters
- Cloud Functions and Cloud Run Services
- Container (GKE) Clusters
- Firewall Rules
- Compute Addresses
- Redis Instances
- Cloud SQL postgres Instances


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
# Generate tfvars with GCP resources (default)
./tf.sh stg r1-rai plan --get-gcp-resources-site primary --target-site dr

# Skip GCP resource generation for faster execution
./tf.sh stg r1-rai plan --get-gcp-resources-site dr --target-site dr

# Generate resources for production environment
./tf.sh prod-us rai plan --get-gcp-resources-site none
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

### Debug Mode

For debugging, run the Python script directly with verbose output:

```bash
python3 -v terraform_wrapper.py --environment stg --cluster r1-rai --action plan
```

## Contributing

1. Follow Python PEP 8 style guidelines
2. Add comprehensive docstrings for new functions
3. Include error handling for all external operations
4. Test with multiple environments and clusters

## License

This project is licensed under the MIT License. 