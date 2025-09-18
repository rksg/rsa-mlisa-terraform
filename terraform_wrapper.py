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

import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Tuple
from enum import Enum
import json


class TerraformAction(Enum):
    """Available Terraform operations."""
    INIT = "init"
    PLAN = "plan"
    APPLY = "apply"
    DESTROY = "destroy"
    OUTPUT = "output"
    SHOW = "show"
    GET_REPLACEMENT_VALUES = "get_replacement_values"


class TerraformWrapper:
    """
    Terraform workspace wrapper with comprehensive environment and DR site support.
    
    Manages Terraform workspaces, executes Terraform commands
    """
    
    def __init__(self, environment: str, cluster: str, target_site: str = "primary"):
        """
        Initialize the Terraform wrapper.
        
        Args:
            environment: Target environment (stg, prod-us, prod-eu, prod-asia)
            cluster: Cluster type (rai, r1-rai)
            target_site: Deployment target (primary or dr)
        """
        self.environment = environment
        self.cluster = cluster
        self.target_site = target_site
        self.workspace_name = f"{environment}-{cluster}-{target_site}"
        
        # Initialize file paths
        self.root_dir = Path(__file__).parent
        self.tf_vars_dir = self.root_dir / "tf-vars"
        self.tfvars_file = self.tf_vars_dir / environment / f"{cluster}.tfvars.json" if self.target_site == "primary" else self.tf_vars_dir / environment / f"{cluster}-dr.tfvars.json"

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
        start_time = time.time()
        command = ["terraform", "apply"]
        
        # Add tfvars file if it exists
        if self.tfvars_file.exists():
            command.extend(["-var-file", str(self.tfvars_file)])
        
        if auto_approve:
            command.append("-auto-approve")
        
        return_code, stdout, stderr = self._run_command(command, capture_output=False)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if return_code != 0:
            print(f"❌ Error running terraform apply: {stderr}")
            print(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
            return False
        
        print("✅ terraform apply completed successfully")
        print(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
        return True

    def _run_terraform_get_replacement_values(self) -> dict[str, str]:
        """Execute terraform get replacement values command."""
        return_code, stdout, stderr = self._run_command(["terraform", "output", "-json"])
        
        if return_code != 0:
            print(f"❌ Error running terraform get replacement values: {stderr}")
            return {}
        
        try:
            output_data = json.loads(stdout)
            hdfs_host = "hdfs://" + output_data["dpc_master_node"]["value"][0]
            hdfs_yarn_rm_host = output_data["dpc_master_node"]["value"][0]
            
            postgresql_druid_host = None
            for key, value in output_data["sql_private_ip_address"]["value"].items():
                if "mlisa-sql-druid" in key:
                    postgresql_druid_host = value["private_ip_address"]
                    break
            
            if postgresql_druid_host is None:
                print("Warning: No PostgreSQL Druid host found")
                postgresql_druid_host = ""
            
            return {"hdfs_host": hdfs_host, "hdfs_yarn_rm_host": hdfs_yarn_rm_host, "postgresql_druid_host": postgresql_druid_host}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON output: {e}")
            return {}
        except KeyError as e:
            print(f"❌ Error accessing expected key in output: {e}")
            return {}

    def _run_terraform_destroy(self, auto_approve: bool = False) -> bool:
        """
        Execute terraform destroy command.
        
        Args:
            auto_approve: Whether to auto-approve changes
            
        Returns:
            True if successful, False otherwise
        """
        print("🗑️  Running terraform destroy...")
        start_time = time.time()
        command = ["terraform", "destroy"]
        
        # Add tfvars file if it exists
        if self.tfvars_file.exists():
            command.extend(["-var-file", str(self.tfvars_file)])
        
        if auto_approve:
            command.append("-auto-approve")
        
        return_code, stdout, stderr = self._run_command(command, capture_output=False)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if return_code != 0:
            print(f"❌ Error running terraform destroy: {stderr}")
            print(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
            return False
        
        print("✅ terraform destroy completed successfully")
        print(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
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
        print(f"{'='*70}\n")
        
        # Verify Terraform installation
        if not self._check_terraform_installed():
            return False
        
        # Execute the requested action
        if action == TerraformAction.INIT:
            return self._run_terraform_init(force=kwargs.get('force', False))
        
        # Manage workspace
        if not self._create_or_switch_workspace():
            return False
        
        # Execute the requested action
        if action == TerraformAction.PLAN:
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
  
  # Plan changes
  python terraform_wrapper.py --environment prod-us --cluster rai --action plan
  
  # Apply changes with auto-approve
  python terraform_wrapper.py --environment prod-eu --cluster r1-rai --action apply --auto-approve
  
  # Destroy infrastructure (with confirmation)
  python terraform_wrapper.py --environment stg --cluster rai --action destroy
  
  # Show current state
  python terraform_wrapper.py --environment prod-asia --cluster r1-rai --action show
  
  # Initialize
  python terraform_wrapper.py --environment stg --cluster r1-rai --action init
  
  # Get replacement values
  python terraform_wrapper.py --environment stg --cluster r1-rai --action get_replacement_values
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
        )
        
        # Execute the requested action
        action = TerraformAction(args.action)

        if action == TerraformAction.GET_REPLACEMENT_VALUES:
            replacement_values = wrapper._run_terraform_get_replacement_values()
            print(replacement_values)
            sys.exit(0)
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