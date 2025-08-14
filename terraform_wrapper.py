#!/usr/bin/env python3
"""
Terraform Workspace Wrapper

A comprehensive Python wrapper for managing Terraform workspaces and operations across multiple environments and clusters.
Supports primary and disaster recovery (DR) site deployments with automatic GCP resource discovery and configuration generation.

Key Features:
- Automated Terraform workspace management
- Multi-environment and cluster support (stg, prod-us, prod-eu, prod-asia)
- Primary/DR site deployment support
- GCP resource discovery and tfvars generation
- Interactive user confirmation for destructive operations
- Comprehensive error handling and logging
"""

import json
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from enum import Enum

# Import the GCP resource reader for automatic resource discovery
from gcp_resource_reader import GCPResourceReader


class TerraformAction(Enum):
    """Available Terraform operations."""
    INIT = "init"
    PLAN = "plan"
    APPLY = "apply"
    DESTROY = "destroy"
    OUTPUT = "output"
    SHOW = "show"


class TerraformWrapper:
    """
    Terraform workspace wrapper with comprehensive environment and DR site support.
    
    Manages Terraform workspaces, executes Terraform commands, and optionally generates
    GCP resource configurations for both primary and disaster recovery sites.
    """
    
    def __init__(self, environment: str, cluster: str, target_site: str = "primary", 
                 refresh_gcp_resource_vars: bool = False):
        """
        Initialize the Terraform wrapper.
        
        Args:
            environment: Target environment (stg, prod-us, prod-eu, prod-asia)
            cluster: Cluster type (rai, r1-rai)
            target_site: Deployment target (primary or dr)
            refresh_gcp_resource_vars: Whether to refresh GCP resource variables
        """
        self.environment = environment
        self.cluster = cluster
        self.target_site = target_site
        self.refresh_gcp_resource_vars = refresh_gcp_resource_vars
        self.workspace_name = f"{environment}-{cluster}-{target_site}"
        
        # Initialize file paths
        self.root_dir = Path(__file__).parent
        self.config_dir = self.root_dir / "configs"
        self.config_file = self.config_dir / "config.json"
        self.tfvars_file_primary = self.config_dir / environment / f"{cluster}.tfvars.json"
        self.tfvars_file_dr = self.config_dir / environment / f"{cluster}-dr.tfvars.json"
        self.tfvars_file = self.tfvars_file_primary if self.target_site == "primary" else self.tfvars_file_dr

        # Load and validate configuration
        self.config = self._load_config()
        self._validate_config()
        
        # Generate GCP resources if requested
        if self.refresh_gcp_resource_vars:
            self._generate_gcp_resources()
        
        # Set Terraform environment variables
        self._set_environment_variables()
    
    def _generate_gcp_resources(self):
        """
        Generate GCP resource configurations and create tfvars files.
        
        Discovers GCP resources using the GCPResourceReader and generates both
        primary and DR site configurations with appropriate IP ranges.
        """
        try:
            print(f"🔍 Generating GCP resources for {self.environment}-{self.cluster}...")
            
            # Load configuration for GCP resource reader
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Initialize GCP resource reader with project and network configuration
            reader = GCPResourceReader(
                project_id=config_data[self.environment]['project_id'],
                network_name=config_data[self.environment][self.cluster]['vpc'],
                region=config_data[self.environment]['region'],
                ip_ranges=config_data[self.environment][self.cluster]['ip_ranges']
            )
            
            # Discover all GCP resources for both primary and DR sites
            resources, resources_dr = reader.get_all_resources()
            
            # Save primary site configuration
            with open(self.tfvars_file_primary, 'w') as f:
                json.dump(resources, f, indent=2)
            
            # Save DR site configuration
            with open(self.tfvars_file_dr, 'w') as f:
                json.dump(resources_dr, f, indent=2)
            
            print(f"✅ GCP resources generated successfully")
            print(f"   Primary: {self.tfvars_file_primary}")
            print(f"   DR Site: {self.tfvars_file_dr}")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to generate GCP resources: {e}")
            raise ValueError(f"Failed to generate GCP resources: {e}")
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def _validate_config(self):
        """Validate environment and cluster configuration."""
        if self.environment not in self.config:
            raise ValueError(f"Environment '{self.environment}' not found in configuration")
        
        env_config = self.config[self.environment]
        if self.cluster not in env_config:
            raise ValueError(f"Cluster '{self.cluster}' not found in environment '{self.environment}'")
        
        # Only validate tfvars file exists if we're not generating it
        if not self.refresh_gcp_resource_vars and not self.tfvars_file.exists():
            raise FileNotFoundError(f"Terraform variables file not found: {self.tfvars_file}")
    
    def _set_environment_variables(self):
        """Set Terraform environment variables based on configuration."""
        env_config = self.config[self.environment]
        
        # Set common environment variables
        os.environ["TF_VAR_project"] = env_config["project_id"]
        os.environ["TF_VAR_environment"] = self.environment
        os.environ["TF_VAR_cluster"] = self.cluster
        os.environ["TF_VAR_target_site"] = self.target_site

        # Set region based on deployment target
        os.environ["TF_VAR_region"] = env_config["dr_region"] if self.target_site == "dr" else env_config["region"]
    
    def _run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Execute a shell command and return the result.
        
        Args:
            command: Command arguments as a list
            capture_output: Whether to capture command output
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                cwd=self.root_dir
            )
            return result.returncode, result.stdout, result.stderr
        except FileNotFoundError:
            return 1, "", f"Command not found: {command[0]}"
        except Exception as e:
            return 1, "", str(e)
    
    def _check_terraform_installed(self) -> bool:
        """Verify Terraform is installed and accessible."""
        return_code, _, stderr = self._run_command(["terraform", "--version"])
        if return_code != 0:
            print(f"❌ Error: Terraform not found or not accessible: {stderr}")
            return False
        return True
    
    def _get_workspace_list(self) -> List[str]:
        """Get list of existing Terraform workspaces."""
        return_code, stdout, stderr = self._run_command(["terraform", "workspace", "list"])
        if return_code != 0:
            print(f"❌ Error getting workspace list: {stderr}")
            return []
        
        # Parse workspace list output (format: * workspace_name or workspace_name)
        workspaces = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                # Remove asterisk indicator and whitespace
                workspace = line.strip().lstrip('* ').strip()
                if workspace:
                    workspaces.append(workspace)
        
        return workspaces
    
    def _create_or_switch_workspace(self) -> bool:
        """
        Create or switch to the target Terraform workspace.
        
        Returns:
            True if successful, False otherwise
        """
        print(f"🏗️  Managing workspace: {self.workspace_name}")
        
        # Get current workspace
        return_code, stdout, stderr = self._run_command(["terraform", "workspace", "show"])
        if return_code != 0:
            print(f"❌ Error getting current workspace: {stderr}")
            return False
        
        current_workspace = stdout.strip()
        print(f"Current workspace: {current_workspace}")
        
        # Get list of existing workspaces
        existing_workspaces = self._get_workspace_list()
        
        if self.workspace_name in existing_workspaces:
            if current_workspace == self.workspace_name:
                print(f"✅ Already in workspace: {self.workspace_name}")
                return True
            else:
                print(f"🔄 Switching to workspace: {self.workspace_name}")
                return_code, _, stderr = self._run_command(["terraform", "workspace", "select", self.workspace_name])
                if return_code != 0:
                    print(f"❌ Error switching workspace: {stderr}")
                    return False
                print(f"✅ Successfully switched to workspace: {self.workspace_name}")
                return True
        else:
            print(f"🆕 Creating new workspace: {self.workspace_name}")
            return_code, _, stderr = self._run_command(["terraform", "workspace", "new", self.workspace_name])
            if return_code != 0:
                print(f"❌ Error creating workspace: {stderr}")
                return False
            print(f"✅ Successfully created and switched to workspace: {self.workspace_name}")
            return True
    
    def _run_terraform_init(self, force: bool = False) -> bool:
        """
        Execute terraform init command.
        
        Args:
            force: Whether to force reinitialization
            
        Returns:
            True if successful, False otherwise
        """
        print("🚀 Running terraform init...")
        
        command = ["terraform", "init"]
        if force:
            command.append("-reconfigure")
        
        return_code, stdout, stderr = self._run_command(command)
        
        if return_code != 0:
            print(f"❌ Error running terraform init: {stderr}")
            return False
        
        print("✅ terraform init completed successfully")
        return True
    
    def _run_terraform_plan(self, detailed: bool = False) -> bool:
        """
        Execute terraform plan command.
        
        Args:
            detailed: Whether to show detailed exit codes
            
        Returns:
            True if successful, False otherwise
        """
        print("📋 Running terraform plan...")
        
        command = ["terraform", "plan"]
        
        # Add tfvars file if it exists
        if self.tfvars_file.exists():
            command.extend(["-var-file", str(self.tfvars_file)])
        
        if detailed:
            command.append("-detailed-exitcode")
        
        return_code, stdout, stderr = self._run_command(command)
        
        if return_code == 0:
            print("✅ terraform plan completed successfully - no changes needed")
            print(stdout)
            return True
        elif return_code == 1:
            print("❌ terraform plan failed:")
            print(stderr)
            return False
        elif return_code == 2:
            print("✅ terraform plan completed successfully - changes detected:")
            print(stdout)
            return True
        else:
            print(f"⚠️  Unexpected return code from terraform plan: {return_code}")
            return False
    
    def _run_terraform_apply(self, auto_approve: bool = False) -> bool:
        """
        Execute terraform apply command.
        
        Args:
            auto_approve: Whether to auto-approve changes
            
        Returns:
            True if successful, False otherwise
        """
        print("🚀 Running terraform apply...")
        
        command = ["terraform", "apply"]
        
        # Add tfvars file if it exists
        if self.tfvars_file.exists():
            command.extend(["-var-file", str(self.tfvars_file)])
        
        if auto_approve:
            command.append("-auto-approve")
        
        return_code, stdout, stderr = self._run_command(command, capture_output=False)
        
        if return_code != 0:
            print(f"❌ Error running terraform apply: {stderr}")
            return False
        
        print("✅ terraform apply completed successfully")
        return True
    
    def _run_terraform_destroy(self, auto_approve: bool = False) -> bool:
        """
        Execute terraform destroy command.
        
        Args:
            auto_approve: Whether to auto-approve changes
            
        Returns:
            True if successful, False otherwise
        """
        print("🗑️  Running terraform destroy...")
        
        command = ["terraform", "destroy"]
        
        # Add tfvars file if it exists
        if self.tfvars_file.exists():
            command.extend(["-var-file", str(self.tfvars_file)])
        
        if auto_approve:
            command.append("-auto-approve")
        
        return_code, stdout, stderr = self._run_command(command, capture_output=False)
        
        if return_code != 0:
            print(f"❌ Error running terraform destroy: {stderr}")
            return False
        
        print("✅ terraform destroy completed successfully")
        return True
    
    def _run_terraform_output(self) -> bool:
        """Execute terraform output command."""
        print("📤 Running terraform output...")
        
        return_code, stdout, stderr = self._run_command(["terraform", "output"])
        
        if return_code != 0:
            print(f"❌ Error running terraform output: {stderr}")
            return False
        
        print("📤 terraform output:")
        print(stdout)
        return True
    
    def _run_terraform_show(self) -> bool:
        """Execute terraform show command."""
        print("📊 Running terraform show...")
        
        return_code, stdout, stderr = self._run_command(["terraform", "show"])
        
        if return_code != 0:
            print(f"❌ Error running terraform show: {stderr}")
            return False
        
        print("📊 terraform show:")
        print(stdout)
        return True
    
    def _confirm_action(self, action: str) -> bool:
        """
        Prompt user for confirmation before executing a destructive action.
        
        Args:
            action: Description of the action to confirm
            
        Returns:
            True if user confirms, False otherwise
        """
        while True:
            response = input(f"\n⚠️  Do you want to proceed with {action}? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def execute_action(self, action: TerraformAction, **kwargs) -> bool:
        """
        Execute the specified Terraform action.
        
        Args:
            action: The Terraform action to execute
            **kwargs: Additional arguments for the action
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"🚀 Terraform Wrapper - {action.value.upper()}")
        print(f"🌍 Environment: {self.environment}")
        print(f"🔧 Cluster: {self.cluster}")
        print(f"🎯 Target Site: {self.target_site}")
        print(f"🏗️  Workspace: {self.workspace_name}")
        print(f"🔄 Refresh GCP Resource Vars: {self.refresh_gcp_resource_vars}")
        print(f"{'='*70}\n")
        
        # Verify Terraform installation
        if not self._check_terraform_installed():
            return False
        
        # Manage workspace
        if not self._create_or_switch_workspace():
            return False
        
        # Execute the requested action
        if action == TerraformAction.INIT:
            return self._run_terraform_init(force=kwargs.get('force', False))
        
        elif action == TerraformAction.PLAN:
            return self._run_terraform_plan(detailed=kwargs.get('detailed', False))
        
        elif action == TerraformAction.APPLY:
            auto_approve = kwargs.get('auto_approve', False)
            if not auto_approve:
                if not self._confirm_action("terraform apply"):
                    print("❌ Operation cancelled by user")
                    return False
            return self._run_terraform_apply(auto_approve=auto_approve)
        
        elif action == TerraformAction.DESTROY:
            auto_approve = kwargs.get('auto_approve', False)
            if not auto_approve:
                if not self._confirm_action("terraform destroy"):
                    print("❌ Operation cancelled by user")
                    return False
            return self._run_terraform_destroy(auto_approve=auto_approve)
        
        elif action == TerraformAction.OUTPUT:
            return self._run_terraform_output()
        
        elif action == TerraformAction.SHOW:
            return self._run_terraform_show()
        
        else:
            print(f"❌ Unknown action: {action}")
            return False


def main():
    """
    Main function to parse command line arguments and execute Terraform operations.
    
    Provides a command-line interface for the Terraform wrapper with support for
    all major Terraform operations and GCP resource management.
    """
    parser = argparse.ArgumentParser(
        description="Terraform Workspace Wrapper with GCP Resource Discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize Terraform workspace
  python terraform_wrapper.py --environment stg --cluster r1-rai --action init
  
  # Plan changes with GCP resource refresh
  python terraform_wrapper.py --environment prod-us --cluster rai --action plan --refresh-gcp-resource-vars
  
  # Apply changes with auto-approve
  python terraform_wrapper.py --environment prod-eu --cluster r1-rai --action apply --auto-approve
  
  # Destroy infrastructure (with confirmation)
  python terraform_wrapper.py --environment stg --cluster rai --action destroy
  
  # Show current state
  python terraform_wrapper.py --environment prod-asia --cluster r1-rai --action show
  
  # Initialize with refreshed GCP resource variables
  python terraform_wrapper.py --environment stg --cluster r1-rai --action init --refresh-gcp-resource-vars
        """
    )
    
    parser.add_argument(
        '--environment',
        required=True,
        choices=['stg', 'prod-us', 'prod-eu', 'prod-asia'],
        help='Target environment for deployment'
    )
    
    parser.add_argument(
        '--cluster',
        required=True,
        choices=['rai', 'r1-rai'],
        help='Cluster type to deploy'
    )
    
    parser.add_argument(
        '--target-site',
        default='primary',
        choices=['primary', 'dr'],
        help='Target deployment site (primary or disaster recovery)'
    )
    
    parser.add_argument(
        '--action',
        required=True,
        choices=[action.value for action in TerraformAction],
        help='Terraform action to perform'
    )
    
    parser.add_argument(
        '--refresh-gcp-resource-vars',
        action='store_true',
        help='Refresh GCP resource variables by generating new tfvars files'
    )
    
    parser.add_argument(
        '--auto-approve',
        action='store_true',
        help='Auto-approve changes (for apply and destroy actions)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reinitialization (for init action)'
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed exit codes (for plan action)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create wrapper instance
        wrapper = TerraformWrapper(
            environment=args.environment,
            cluster=args.cluster,
            target_site=args.target_site,
            refresh_gcp_resource_vars=args.refresh_gcp_resource_vars
        )
        
        # Execute the requested action
        action = TerraformAction(args.action)
        success = wrapper.execute_action(
            action,
            auto_approve=args.auto_approve,
            force=args.force,
            detailed=args.detailed
        )
        
        if success:
            print(f"\n✅ {action.value.upper()} completed successfully")
            sys.exit(0)
        else:
            print(f"\n❌ {action.value.upper()} failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 