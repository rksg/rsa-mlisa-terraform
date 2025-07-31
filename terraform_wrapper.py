#!/usr/bin/env python3
"""
Terraform Workspace Wrapper

This script provides a wrapper around Terraform operations with workspace management.
It supports:
- Creating/switching to Terraform workspaces
- Running terraform init, plan, and apply
- Environment and cluster-specific configurations
- Interactive mode for user confirmation
- GCP resource discovery and tfvars generation
"""

import json
import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Import the GCP resource reader
from gcp_resource_reader import GCPResourceReader


class TerraformAction(Enum):
    """Enumeration of available Terraform actions."""
    INIT = "init"
    PLAN = "plan"
    APPLY = "apply"
    DESTROY = "destroy"
    OUTPUT = "output"
    SHOW = "show"


class TerraformWrapper:
    """
    Wrapper class for Terraform operations with workspace management.
    
    This class provides methods to manage Terraform workspaces and execute
    Terraform commands with proper error handling and user interaction.
    """
    
    def __init__(self, environment: str, cluster: str, target_site: str = "primary", get_gcp_resources_site: str = "none"):
        """
        Initialize the Terraform wrapper.
        
        Args:
            environment: The environment (stg, prod-us, prod-eu, prod-asia)
            cluster: The cluster type (rai, r1-rai)
            target_site: The target site (primary, dr)
            get_gcp_resources: Whether to get GCP resources to generate tfvars file
        """
        self.environment = environment
        self.cluster = cluster
        self.target_site = target_site
        self.get_gcp_resources_site = get_gcp_resources_site
        self.workspace_name = f"{environment}-{cluster}-{target_site}"
        
        # Set up paths
        self.root_dir = Path(__file__).parent
        self.config_dir = self.root_dir / "configs"
        self.config_file = self.config_dir / "config.json"
        self.tfvars_file = self.config_dir / environment / f"{cluster}.tfvars.json"
        
        # Load configuration
        self.config = self._load_config()
        
        # Validate configuration
        self._validate_config()
        
        # Generate GCP resources and tfvars file if requested
        if self.get_gcp_resources_site != "none":
            self._generate_gcp_resources(self.get_gcp_resources_site)
        else:
            pass
        
        # Set environment variables for Terraform
        self._set_environment_variables()
    
    def _generate_gcp_resources(self, site: str):
        """Generate GCP resources and create tfvars file."""
        try:
            print(f"Generating GCP resources for {self.environment}-{self.cluster}...")
            
            # Load configuration for GCP resource reader
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Create GCP resource reader
            if site == "primary":
                reader = GCPResourceReader(
                    project_id=config_data[self.environment]['project_id'],
                    network_name=config_data[self.environment][self.cluster]['vpc'],
                    region=config_data[self.environment]['region']
                )
            elif site == "dr":
                reader = GCPResourceReader(
                    project_id=config_data[self.environment]['dr_project_id'],
                    network_name=config_data[self.environment][self.cluster]['vpc'],
                    region=config_data[self.environment]['dr_region']
                )
            
            # Get all resources
            resources = reader.get_all_resources()
            
            
            # Save results to JSON file
            output_filename = self.tfvars_file
            with open(output_filename, 'w') as f:
                json.dump(resources, f, indent=2)
            
            print(f"✅ GCP resources saved to: {output_filename}")
            
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
        """Validate that the environment and cluster exist in configuration."""
        if self.environment not in self.config:
            raise ValueError(f"Environment '{self.environment}' not found in configuration")
        
        env_config = self.config[self.environment]
        if self.cluster not in env_config:
            raise ValueError(f"Cluster '{self.cluster}' not found in environment '{self.environment}'")
        
        # Only validate tfvars file exists if we're not generating it
        if not self.get_gcp_resources_site and not self.tfvars_file.exists():
            raise FileNotFoundError(f"Terraform variables file not found: {self.tfvars_file}")
    
    def _set_environment_variables(self):
        """Set environment variables for Terraform."""
        env_config = self.config[self.environment]
        
        # Set project and region based on target site
        if self.target_site == "dr":
            os.environ["TF_VAR_project"] = env_config.get("dr_project_id", env_config["project_id"])
            os.environ["TF_VAR_region"] = env_config.get("dr_region", env_config["region"])
        else:
            os.environ["TF_VAR_project"] = env_config["project_id"]
            os.environ["TF_VAR_region"] = env_config["region"]
        
        # Set other common variables
        os.environ["TF_VAR_environment"] = self.environment
        os.environ["TF_VAR_cluster"] = self.cluster
        os.environ["TF_VAR_target_site"] = self.target_site
    
    def _run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Run a command and return the result.
        
        Args:
            command: List of command arguments
            capture_output: Whether to capture output
            
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
        """Check if Terraform is installed and available."""
        return_code, _, stderr = self._run_command(["terraform", "--version"])
        if return_code != 0:
            print(f"Error: Terraform not found or not accessible: {stderr}")
            return False
        return True
    
    def _get_workspace_list(self) -> List[str]:
        """Get list of existing Terraform workspaces."""
        return_code, stdout, stderr = self._run_command(["terraform", "workspace", "list"])
        if return_code != 0:
            print(f"Error getting workspace list: {stderr}")
            return []
        
        # Parse workspace list (format: * workspace_name or workspace_name)
        workspaces = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                # Remove asterisk and whitespace
                workspace = line.strip().lstrip('* ').strip()
                if workspace:
                    workspaces.append(workspace)
        
        return workspaces
    
    def _create_or_switch_workspace(self) -> bool:
        """
        Create or switch to the target workspace.
        
        Returns:
            True if successful, False otherwise
        """
        print(f"Managing workspace: {self.workspace_name}")
        
        # Get current workspace
        return_code, stdout, stderr = self._run_command(["terraform", "workspace", "show"])
        if return_code != 0:
            print(f"Error getting current workspace: {stderr}")
            return False
        
        current_workspace = stdout.strip()
        print(f"Current workspace: {current_workspace}")
        
        # Get list of existing workspaces
        existing_workspaces = self._get_workspace_list()
        
        if self.workspace_name in existing_workspaces:
            if current_workspace == self.workspace_name:
                print(f"Already in workspace: {self.workspace_name}")
                return True
            else:
                print(f"Switching to workspace: {self.workspace_name}")
                return_code, _, stderr = self._run_command(["terraform", "workspace", "select", self.workspace_name])
                if return_code != 0:
                    print(f"Error switching workspace: {stderr}")
                    return False
                print(f"Successfully switched to workspace: {self.workspace_name}")
                return True
        else:
            print(f"Creating new workspace: {self.workspace_name}")
            return_code, _, stderr = self._run_command(["terraform", "workspace", "new", self.workspace_name])
            if return_code != 0:
                print(f"Error creating workspace: {stderr}")
                return False
            print(f"Successfully created and switched to workspace: {self.workspace_name}")
            return True
    
    def _run_terraform_init(self, force: bool = False) -> bool:
        """
        Run terraform init.
        
        Args:
            force: Whether to force reinitialization
            
        Returns:
            True if successful, False otherwise
        """
        print("Running terraform init...")
        
        command = ["terraform", "init"]
        if force:
            command.append("-reconfigure")
        
        return_code, stdout, stderr = self._run_command(command)
        
        if return_code != 0:
            print(f"Error running terraform init: {stderr}")
            return False
        
        print("terraform init completed successfully")
        return True
    
    def _run_terraform_plan(self, detailed: bool = False) -> bool:
        """
        Run terraform plan.
        
        Args:
            detailed: Whether to show detailed output
            
        Returns:
            True if successful, False otherwise
        """
        print("Running terraform plan...")
        
        command = ["terraform", "plan"]
        
        # Add tfvars file if it exists
        if self.tfvars_file.exists():
            command.extend(["-var-file", str(self.tfvars_file)])
        
        if detailed:
            command.append("-detailed-exitcode")
        
        return_code, stdout, stderr = self._run_command(command)
        
        if return_code == 0:
            print("terraform plan completed successfully - no changes needed")
            print(stdout)
            return True
        elif return_code == 1:
            print("terraform plan failed:")
            print(stderr)
            return False
        elif return_code == 2:
            print("terraform plan completed successfully - changes detected:")
            print(stdout)
            return True
        else:
            print(f"Unexpected return code from terraform plan: {return_code}")
            return False
    
    def _run_terraform_apply(self, auto_approve: bool = False) -> bool:
        """
        Run terraform apply.
        
        Args:
            auto_approve: Whether to auto-approve changes
            
        Returns:
            True if successful, False otherwise
        """
        print("Running terraform apply...")
        
        command = ["terraform", "apply"]
        
        # Add tfvars file if it exists
        if self.tfvars_file.exists():
            command.extend(["-var-file", str(self.tfvars_file)])
        
        if auto_approve:
            command.append("-auto-approve")
        
        return_code, stdout, stderr = self._run_command(command, capture_output=False)
        
        if return_code != 0:
            print(f"Error running terraform apply: {stderr}")
            return False
        
        print("terraform apply completed successfully")
        return True
    
    def _run_terraform_destroy(self, auto_approve: bool = False) -> bool:
        """
        Run terraform destroy.
        
        Args:
            auto_approve: Whether to auto-approve changes
            
        Returns:
            True if successful, False otherwise
        """
        print("Running terraform destroy...")
        
        command = ["terraform", "destroy"]
        
        # Add tfvars file if it exists
        if self.tfvars_file.exists():
            command.extend(["-var-file", str(self.tfvars_file)])
        
        if auto_approve:
            command.append("-auto-approve")
        
        return_code, stdout, stderr = self._run_command(command, capture_output=False)
        
        if return_code != 0:
            print(f"Error running terraform destroy: {stderr}")
            return False
        
        print("terraform destroy completed successfully")
        return True
    
    def _run_terraform_output(self) -> bool:
        """Run terraform output."""
        print("Running terraform output...")
        
        return_code, stdout, stderr = self._run_command(["terraform", "output"])
        
        if return_code != 0:
            print(f"Error running terraform output: {stderr}")
            return False
        
        print("terraform output:")
        print(stdout)
        return True
    
    def _run_terraform_show(self) -> bool:
        """Run terraform show."""
        print("Running terraform show...")
        
        return_code, stdout, stderr = self._run_command(["terraform", "show"])
        
        if return_code != 0:
            print(f"Error running terraform show: {stderr}")
            return False
        
        print("terraform show:")
        print(stdout)
        return True
    
    def _confirm_action(self, action: str) -> bool:
        """
        Ask user for confirmation before executing an action.
        
        Args:
            action: Description of the action to confirm
            
        Returns:
            True if user confirms, False otherwise
        """
        while True:
            response = input(f"\nDo you want to proceed with {action}? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def execute_action(self, action: TerraformAction, **kwargs) -> bool:
        """
        Execute a Terraform action.
        
        Args:
            action: The Terraform action to execute
            **kwargs: Additional arguments for the action
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"Terraform Wrapper - {action.value.upper()}")
        print(f"Environment: {self.environment}")
        print(f"Cluster: {self.cluster}")
        print(f"Target Site: {self.target_site}")
        print(f"Workspace: {self.workspace_name}")
        print(f"GCP Resources Site: {self.get_gcp_resources_site}")
        print(f"{'='*60}\n")
        
        # Check if Terraform is installed
        if not self._check_terraform_installed():
            return False
        
        # Create or switch to workspace
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
                    print("Operation cancelled by user")
                    return False
            return self._run_terraform_apply(auto_approve=auto_approve)
        
        elif action == TerraformAction.DESTROY:
            auto_approve = kwargs.get('auto_approve', False)
            if not auto_approve:
                if not self._confirm_action("terraform destroy"):
                    print("Operation cancelled by user")
                    return False
            return self._run_terraform_destroy(auto_approve=auto_approve)
        
        elif action == TerraformAction.OUTPUT:
            return self._run_terraform_output()
        
        elif action == TerraformAction.SHOW:
            return self._run_terraform_show()
        
        else:
            print(f"Unknown action: {action}")
            return False


def main():
    """
    Main function to parse arguments and execute Terraform operations.
    """
    parser = argparse.ArgumentParser(
        description="Terraform Workspace Wrapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize Terraform workspace
  python terraform_wrapper.py --environment stg --cluster r1-rai --action init
  
  # Plan changes
  python terraform_wrapper.py --environment prod-us --cluster rai --action plan
  
  # Apply changes with auto-approve
  python terraform_wrapper.py --environment prod-eu --cluster r1-rai --action apply --auto-approve
  
  # Destroy infrastructure
  python terraform_wrapper.py --environment stg --cluster rai --action destroy
  
  # Show current state
  python terraform_wrapper.py --environment prod-asia --cluster r1-rai --action show
        """
    )
    
    parser.add_argument(
        '--environment',
        required=True,
        choices=['stg', 'prod-us', 'prod-eu', 'prod-asia'],
        help='Environment to deploy to'
    )
    
    parser.add_argument(
        '--cluster',
        required=True,
        choices=['rai', 'r1-rai'],
        help='Cluster type'
    )
    
    parser.add_argument(
        '--target-site',
        default='primary',
        choices=['primary', 'dr'],
        help='Target site (primary or disaster recovery)'
    )
    
    parser.add_argument(
        '--action',
        required=True,
        choices=[action.value for action in TerraformAction],
        help='Terraform action to perform'
    )
    
    parser.add_argument(
        '--get-gcp-resources-site',
        type=str,
        default='none',
        choices=['primary', 'dr', 'none'],
        help='Get GCP resources from site (primary, dr, none) to generate tfvars file'
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
        # Convert get_gcp_resources string to boolean
        get_gcp_resources_site = args.get_gcp_resources_site.lower()
        
        # Create wrapper instance
        wrapper = TerraformWrapper(
            environment=args.environment,
            cluster=args.cluster,
            target_site=args.target_site,
            get_gcp_resources_site=get_gcp_resources_site
        )
        
        # Execute the action
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
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 