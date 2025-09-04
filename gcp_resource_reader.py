
"""
Google Cloud Resource Properties Reader

This script reads properties of various Google Cloud resources using gcloud CLI:
- Compute Networks and Subnetworks
- NAT Routers
- DataProc Clusters
- Cloud Functions
- Cloud Run Services
- Container (GKE) Clusters
- Firewall Rules
- Compute Addresses
- Redis Instances
- Cloud SQL PostgreSQL Instances

The script filters resources based on a specific VPC network and generates both primary and DR configurations.
"""

import json
import subprocess
import datetime
import re
import ipaddress
from typing import Dict, List, Any, Optional, Tuple


class GCPResourceReader:
    """
    GCP Resource Reader using gcloud CLI for resource discovery.
    
    This class provides methods to fetch and filter GCP resources using gcloud CLI commands,
    avoiding SSL certificate issues that commonly occur in corporate environments.
    
    Features:
    - Automatic resource discovery for primary and DR sites
    - IP range management for multi-site deployments
    - Gateway address calculation for subnetworks
    - Comprehensive resource filtering and validation
    """
    
    def __init__(self, project_id: Optional[str] = None, 
                 network_name: Optional[str] = None, 
                 region: Optional[str] = None,
                 dr_region: Optional[str] = None,
                 ip_ranges: Optional[str] = None):
        """
        Initialize the GCP Resource Reader.
        
        Args:
            project_id: Google Cloud project ID. If None, will try to get from environment
            network_name: Name of the VPC network to filter resources
            region: GCP region for regional resources
            ip_ranges: IP range configuration for primary and DR sites
        """
        self.project_id = project_id
        self.network_name = network_name
        self.region = region
        self.dr_region = dr_region
        self.ip_ranges = ip_ranges
        self.subnetwork_name = 'default'
        
        # Validate project and network
        self._check_project_id_and_network_name()
        
        # Construct network filter for gcloud CLI calls
        self.network_filter = f"network = \"https://www.googleapis.com/compute/v1/projects/{self.project_id}/global/networks/{self.network_name}\""

    def _check_project_id_and_network_name(self):
        """
        Validate project ID and network name using gcloud CLI.
        
        Raises:
            ValueError: If project or network is not found or accessible
        """
        # Check project ID
        if self.project_id:
            try:
                print(f"Checking project ID: {self.project_id}")
                result = subprocess.run(
                    ['gcloud', 'projects', 'list', f'--filter=projectId={self.project_id}'], 
                    capture_output=True, text=True, check=True
                )
                if result.returncode != 0 or result.stdout.strip() == "":
                    raise ValueError(f"Project ID '{self.project_id}' not found or not accessible.")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error checking project: {e}")
                raise ValueError(f"Project ID '{self.project_id}' not found or not accessible.")
        
        # Check network name if provided
        if self.network_name:
            try:
                print(f"Checking network name: {self.network_name} in project {self.project_id}")
                result = subprocess.run([
                    'gcloud', 'compute', 'networks', 'list', 
                    '--project', self.project_id, 
                    f'--filter=name={self.network_name}'
                ], capture_output=True, text=True, check=True)
                if result.returncode != 0 or result.stdout.strip() == "":
                    raise ValueError(f"Network name '{self.network_name}' not found in project '{self.project_id}'.")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error checking network: {e}")
                raise ValueError(f"Network name '{self.network_name}' not found in project '{self.project_id}'.")
    
    def get_compute_subnetworks(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discover compute subnetworks for both primary and DR sites.
        
        Uses gcloud CLI to fetch subnetworks and creates primary/DR configurations
        with appropriate IP ranges and gateway addresses.
        
        Returns:
            Tuple of (primary_subnetworks, dr_subnetworks) lists containing:
            - name: Subnetwork name (DR version gets '-dr' suffix)
            - description: Subnetwork description
            - ip_cidr_range: IP range from configuration (primary or DR)
            - gateway_address: Calculated gateway address
            - private_ip_google_access: Google access configuration
            - secondary_ip_range: Secondary IP ranges for GKE pods/services
        """
        subnetworks = []
        dr_subnetworks = []
        
        try:
            # Use gcloud CLI to fetch subnetworks for the specified network
            result = subprocess.run([
                'gcloud', 'compute', 'networks', 'subnets', 'list',
                '--project', self.project_id,
                '--filter', self.network_filter,
                '--format', 'json'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for subnetwork in json.loads(result.stdout):
                    # Check if subnetwork has secondary IP ranges (GKE requirement)
                    if subnetwork.get('secondaryIpRanges'):
                        self.subnetwork_name = subnetwork['name']
                        
                        # Create primary subnetwork configuration
                        subnetwork_info = {
                            'name': subnetwork['name'],
                            'description': subnetwork.get('description', ''),
                            'ip_cidr_range': self.ip_ranges.get('primary', {}).get('subnet_ip_cidr_range', ''),
                            'gateway_address': self._get_gateway_address(self.ip_ranges.get('primary', {}).get('subnet_ip_cidr_range', '')),
                            'private_ip_google_access': subnetwork.get('privateIpGoogleAccess', False),
                            'secondary_ip_range': [
                                {
                                    'name': range['rangeName'],
                                    'ip_cidr_range': self.ip_ranges.get('primary', {}).get('secondary_ip_range_pod', '') if range['rangeName'].endswith('pod') else self.ip_ranges.get('primary', {}).get('secondary_ip_range_svc', '')
                                } for range in subnetwork.get('secondaryIpRanges', [])
                            ]
                        }
                        subnetworks.append(subnetwork_info)
                        
                        # Create DR subnetwork configuration with '-dr' suffix
                        dr_subnetwork_info = {
                            'name': subnetwork['name'] + '-dr',
                            'description': subnetwork.get('description', ''),
                            'ip_cidr_range': self.ip_ranges.get('dr', {}).get('subnet_ip_cidr_range', ''),
                            'gateway_address': self._get_gateway_address(self.ip_ranges.get('dr', {}).get('subnet_ip_cidr_range', '')),
                            'private_ip_google_access': subnetwork.get('privateIpGoogleAccess', False),
                            'secondary_ip_range': [
                                {
                                    'name': range['rangeName'] + '-dr',
                                    'ip_cidr_range': self.ip_ranges.get('dr', {}).get('secondary_ip_range_pod', '') if range['rangeName'].endswith('pod') else self.ip_ranges.get('dr', {}).get('secondary_ip_range_svc', '')
                                } for range in subnetwork.get('secondaryIpRanges', [])
                            ]
                        }
                        dr_subnetworks.append(dr_subnetwork_info)
                    else:
                        # Handle subnetworks without secondary IP ranges (VPC connectors, etc.)
                        subnetwork_info = {
                            'name': subnetwork['name'],
                            'description': subnetwork.get('description', ''),
                            'ip_cidr_range': self.ip_ranges.get('primary', {}).get('vpc_connector_ip_cidr_range', ''),
                            'gateway_address': self._get_gateway_address(self.ip_ranges.get('primary', {}).get('vpc_connector_ip_cidr_range', '')),
                            'private_ip_google_access': subnetwork.get('privateIpGoogleAccess', False),
                            'secondary_ip_range': []
                        }
                        subnetworks.append(subnetwork_info)
                        
                        # Create DR version for VPC connector subnetworks
                        dr_subnetwork_info = {
                            'name': subnetwork['name'] + '-dr',
                            'description': subnetwork.get('description', ''),
                            'ip_cidr_range': self.ip_ranges.get('dr', {}).get('vpc_connector_ip_cidr_range', ''),
                            'gateway_address': self._get_gateway_address(self.ip_ranges.get('dr', {}).get('vpc_connector_ip_cidr_range', '')),
                            'private_ip_google_access': subnetwork.get('privateIpGoogleAccess', False),
                            'secondary_ip_range': []
                        }
                        dr_subnetworks.append(dr_subnetwork_info)
        except Exception as e:
            print(f"Error getting compute subnetworks: {e}")
            raise ValueError(f"Error getting compute subnetworks: {e}")
            
        return subnetworks, dr_subnetworks
    
    def _get_gateway_address(self, ip_cidr_range: str) -> str:
        """
        Calculate the gateway address for a given IP CIDR range.
        
        The gateway address is the first usable IP address in the subnet.
        This is typically used as the default gateway for VMs in the subnet.
        
        Examples:
            - 10.120.46.0/28 → gateway: 10.120.46.1
            - 10.0.0.0/24 → gateway: 10.0.0.1
            - 192.168.1.0/26 → gateway: 192.168.1.1
        
        Args:
            ip_cidr_range: The IP CIDR range string (e.g., "10.0.0.0/24")
            
        Returns:
            The gateway address (e.g., "10.0.0.1") or "N/A" if invalid
            
        Note:
            For /32 networks (single IP), returns "N/A" as no gateway is possible.
        """
        try:
            # Parse the IP network
            network = ipaddress.ip_network(ip_cidr_range, strict=False)
            
            # Calculate gateway address (first usable IP)
            gateway = network.network_address + 1
            
            # Validate that the gateway is within the network range
            if gateway in network:
                return str(gateway)
            else:
                print(f"Warning: Calculated gateway {gateway} is not in network {network}")
                return "N/A"
                
        except ValueError as e:
            print(f"Invalid IP CIDR range '{ip_cidr_range}': {e}")
            return "N/A"
        except Exception as e:
            print(f"Unexpected error calculating gateway for '{ip_cidr_range}': {e}")
            return "N/A"
    
    def get_nat_routers(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Discover NAT routers for both primary and DR sites.
        
        Uses gcloud CLI to fetch NAT routers and creates primary/DR configurations.
        DR routers get '-dr' suffix for easy identification and deployment.
        
        Returns:
            Tuple of (primary_routers, dr_routers) dictionaries containing:
            - name: Router name (DR version gets '-dr' suffix)
            - description: Router description
            - nat: NAT configuration including name, allocation options, and logging
        """
        routers = {}
        dr_routers = {}
        
        try:
            # Use gcloud CLI to fetch NAT routers for the specified network
            result = subprocess.run([
                'gcloud', 'compute', 'routers', 'list',
                '--project', self.project_id,
                '--regions', self.region,
                '--filter', self.network_filter,
                '--format', 'json'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for router in json.loads(result.stdout):
                    # Create primary NAT router configuration
                    router_info = {
                        'name': router['name'],
                        'description': router.get('description', ''),
                        'nat': {
                            'name': router['nats'][0]['name'],
                            'nat_ip_allocate_option': router['nats'][0].get('natIpAllocateOption', ''),
                            'source_subnetwork_ip_ranges_to_nat': router['nats'][0].get('sourceSubnetworkIpRangesToNat', ''),
                            'max_ports_per_vm': router['nats'][0].get('maxPortsPerVm', 0),
                            'log_config': {
                                'enable': router['nats'][0].get('logConfig', {}).get('enable', False),
                                'filter': router['nats'][0].get('logConfig', {}).get('filter', '')
                            } if router['nats'][0].get('logConfig') else None,
                        } if router.get('nats') else []
                    }
                    routers[router['name']] = router_info
                    
                    # Create DR NAT router configuration with '-dr' suffix
                    dr_router_info = {
                        'name': router['name'] + '-dr',
                        'description': router.get('description', ''),
                        'nat': {
                            'name': router['nats'][0]['name'] + '-dr',
                            'nat_ip_allocate_option': router['nats'][0].get('natIpAllocateOption', ''),
                            'source_subnetwork_ip_ranges_to_nat': router['nats'][0].get('sourceSubnetworkIpRangesToNat', ''),
                            'max_ports_per_vm': router['nats'][0].get('maxPortsPerVm', 0),
                            'log_config': {
                                'enable': router['nats'][0].get('logConfig', {}).get('enable', False),
                                'filter': router['nats'][0].get('logConfig', {}).get('filter', '')
                            } if router['nats'][0].get('logConfig') else None,
                        } if router.get('nats') else []
                    }
                    dr_routers[router['name'] + '-dr'] = dr_router_info
                
        except Exception as e:
            print(f"Error getting NAT routers: {e}")
            raise ValueError(f"Error getting NAT routers: {e}")
        return routers, dr_routers

    def _extract_dataproc_labels(self) -> Dict[str, str]:
        """ 
        Returns:
            Dictionary of fixed labels
        """
        labels = {
            "application": "druid",
            "product": "mlisa"
        }
        return labels

    def get_dataproc_clusters(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Discover DataProc clusters for both primary and DR sites.
        
        Uses gcloud CLI to fetch DataProc clusters and creates primary/DR configurations.
        DR clusters get '-dr' suffix for easy identification and deployment.
        
        Returns:
            Tuple of (primary_cluster, dr_cluster) dictionaries containing:
            - cluster_name: Cluster name (DR version gets '-dr' suffix)
            - labels: Cluster labels (filtered)
            - cluster_config: Complete cluster configuration including:
              - gce_cluster_config: GCE-specific configuration
              - master_config: Master node configuration
              - worker_config: Worker node configuration
              - software_config: Software and properties configuration
        """
        primary_cluster = {}
        dr_cluster = {}
        
        try:
            result = subprocess.run([
                'gcloud', 'dataproc', 'clusters', 'list', 
                '--region', self.region, '--project', self.project_id, '--format=json'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for cluster in json.loads(result.stdout):
                    # Filter clusters by subnetwork
                    cluster_subnetwork = cluster['config']['gceClusterConfig']['subnetworkUri'].rsplit('/', 1)[-1]
                    if cluster_subnetwork == self.subnetwork_name:
                        # Create primary DataProc cluster configuration
                        primary_cluster = {
                            'cluster_name': cluster['clusterName'],
                            'labels': self._extract_dataproc_labels(),
                            'cluster_config': {
                                'gce_cluster_config': {
                                    'internal_ip_only': cluster['config']['gceClusterConfig'].get('internalIpOnly'),
                                    'subnetwork': cluster_subnetwork,
                                    'tags': cluster['config']['gceClusterConfig'].get('tags')
                                } if cluster['config'].get('gceClusterConfig') else None,
                                'master_config': self._extract_dataproc_node_config(cluster['config'].get('masterConfig')),
                                'worker_config': self._extract_dataproc_node_config(cluster['config'].get('workerConfig')),
                                'software_config': self._extract_software_config(cluster['config'].get('softwareConfig'))
                            }
                        }
                        
                        # Create DR DataProc cluster configuration with '-dr' suffix
                        dr_cluster = {
                            'cluster_name': cluster['clusterName'] + '-dr',
                            'labels': self._extract_dataproc_labels(),
                            'cluster_config': {
                                'gce_cluster_config': {
                                    'internal_ip_only': cluster['config']['gceClusterConfig'].get('internalIpOnly'),
                                    'subnetwork': cluster_subnetwork + '-dr',  # DR subnetwork gets '-dr' suffix
                                    'tags': [cluster['config']['gceClusterConfig'].get('tags')[0] + '-dr'] if cluster['config'].get('gceClusterConfig').get('tags') else None
                                } if cluster['config'].get('gceClusterConfig') else None,
                                'master_config': self._extract_dataproc_node_config(cluster['config'].get('masterConfig')),
                                'worker_config': self._extract_dataproc_node_config(cluster['config'].get('workerConfig')),
                                'software_config': self._extract_software_config(cluster['config'].get('softwareConfig'))
                            }
                        }
                        # Return only the first cluster found
                        break
        except Exception as e:
            print(f"Error getting DataProc clusters: {e}")
            raise ValueError(f"Error getting DataProc clusters: {e}")
        return primary_cluster, dr_cluster

    def _extract_dataproc_node_config(self, node_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract DataProc node configuration.
        
        Args:
            node_config: Raw node configuration from API
            
        Returns:
            Processed node configuration or None
        """
        if not node_config:
            return None
            
        return {
            'num_instances': node_config.get('numInstances'),
            'machine_type': node_config.get('machineTypeUri').rsplit('/', 1)[-1] if node_config.get('machineTypeUri') else None,
            'image': node_config.get('imageUri').rsplit('/', 1)[-1] if node_config.get('imageUri') else None,
            'preemptibility': node_config.get('preemptibility'),
            'disk_config': {
                'boot_disk_size_gb': node_config.get('diskConfig', {}).get('bootDiskSizeGb'),
                'boot_disk_type': node_config.get('diskConfig', {}).get('bootDiskType'),
            } if node_config.get('diskConfig') else None,
        }

    def _extract_software_config(self, software_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract DataProc software configuration.
        
        Args:
            software_config: Raw software configuration from API
            
        Returns:
            Processed software configuration or None
        """
        if not software_config:
            return None
            
        properties = software_config.get('properties', {})
        return {
            'image_version': software_config.get('imageVersion'),
            'properties': {
                "dataproc:dataproc.monitoring.stackdriver.enable": properties.get('dataproc:dataproc.monitoring.stackdriver.enable'),
                "mapred:mapreduce.map.speculative": properties.get('mapred:mapreduce.map.speculative'),
                "mapred:mapreduce.reduce.speculative": properties.get('mapred:mapreduce.reduce.speculative'),
                "spark:spark.eventLog.enabled": properties.get('spark:spark.eventLog.enabled'),
                "yarn:yarn.nodemanager.resource.cpu-vcores": properties.get('yarn:yarn.nodemanager.resource.cpu-vcores')
            } if properties else None,
        }
    
    def get_cloudfunctions(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discover Cloud Functions for both primary and DR sites.
        
        Uses gcloud CLI to fetch Cloud Functions and creates primary/DR configurations.
        DR functions get '-dr' suffix for easy identification and deployment.
        
        Returns:
            Tuple of (primary_functions, dr_functions) lists containing:
            - name: Function name (DR version gets '-dr' suffix)
            - runtime: Function runtime environment
            - available_memory_mb: Memory allocation
            - source_archive_bucket: Source code bucket
            - source_archive_object: Source code object path
            - timeout: Function timeout
            - entry_point: Function entry point
            - trigger_http: HTTP trigger configuration
            - vpc_connector: VPC connector (DR version gets '-dr' suffix)
            - vpc_connector_egress_settings: Egress settings
            - environment_variables: Function environment variables
            - min_instances: Minimum instance count
            - max_instances: Maximum instance count
        """
        primary_functions = []
        dr_functions = []
        vpc_connector_filter = f"vpcConnector = \"projects/{self.project_id}/locations/{self.region}/connectors/{self.subnetwork_name}-func\""
        
        try:
            result = subprocess.run([
                'gcloud', 'functions', 'list', '--format=json', '--filter', vpc_connector_filter, '--project', self.project_id
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for function in json.loads(result.stdout):
                    # Create primary Cloud Function configuration
                    primary_function_info = {
                        'name': function['name'].rsplit('/', 1)[-1],
                        'runtime': function['runtime'],
                        'available_memory_mb': function['availableMemoryMb'],
                        'source_archive_bucket': function['sourceArchiveUrl'].rsplit('/')[2],
                        'source_archive_object': "/".join(function['sourceArchiveUrl'].rsplit('/')[3:]),
                        'timeout': function['timeout'].rsplit('s', 1)[0],
                        'entry_point': function['entryPoint'],
                        'trigger_http': True,  # Cloud Functions with VPC connector are HTTP triggered
                        'vpc_connector': function['vpcConnector'].rsplit('/', 1)[-1],
                        'vpc_connector_egress_settings': "PRIVATE_RANGES_ONLY",
                        'environment_variables': function.get('environmentVariables', {}),
                        'min_instances': function.get('minInstances', 0),
                        'max_instances': function.get('maxInstances', 0)
                    }
                    primary_functions.append(primary_function_info)
                    
                    # Create DR Cloud Function configuration with '-dr' suffix
                    dr_function_info = {
                        'name': function['name'].rsplit('/', 1)[-1] + '-dr',
                        'runtime': function['runtime'],
                        'available_memory_mb': function['availableMemoryMb'],
                        'source_archive_bucket': function['sourceArchiveUrl'].rsplit('/')[2],
                        'source_archive_object': "/".join(function['sourceArchiveUrl'].rsplit('/')[3:]),
                        'timeout': function['timeout'].rsplit('s', 1)[0],
                        'entry_point': function['entryPoint'],
                        'trigger_http': True,  # Cloud Functions with VPC connector are HTTP triggered
                        'vpc_connector': function['vpcConnector'].rsplit('/', 1)[-1] + '-dr',
                        'vpc_connector_egress_settings': "PRIVATE_RANGES_ONLY",
                        'environment_variables': function.get('environmentVariables', {}),
                        'min_instances': function.get('minInstances', 0),
                        'max_instances': function.get('maxInstances', 0)
                    }
                    dr_functions.append(dr_function_info)
        except Exception as e:
            print(f"Error getting Cloud Functions: {e}")
            raise ValueError(f"Error getting Cloud Functions: {e}")
        return primary_functions, dr_functions
    
    def get_cloudrun(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discover Cloud Run services for both primary and DR sites.
        
        Uses gcloud CLI to fetch Cloud Run services and creates primary/DR configurations.
        DR services get '-dr' suffix for easy identification and deployment.
        
        Returns:
            Tuple of (primary_services, dr_services) lists containing:
            - name: Service name (DR version gets '-dr' suffix)
            - template: Service template configuration including:
              - metadata: Annotations and metadata
              - spec: Service specification with containers, timeout, concurrency
            - traffic: Traffic routing configuration
        """
        primary_services = []
        dr_services = []
        
        try:
            result = subprocess.run([
                'gcloud', 'run', 'services', 'list', '--format=json', '--project', self.project_id
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for service in json.loads(result.stdout):
                    # Filter services by VPC connector annotation
                    annotations = service['spec']['template']['metadata'].get('annotations', {})
                    vpc_connector = annotations.get('run.googleapis.com/vpc-access-connector')
                    
                    if vpc_connector == f'{self.subnetwork_name}-func':
                        # Create primary Cloud Run service configuration
                        primary_service_info = {
                            'name': service['metadata']['name'],
                            'template': {
                                'metadata': {
                                    'annotations': {
                                        'autoscaling.knative.dev/maxScale': '1000',
                                        'run.googleapis.com/client-name': 'terraform',
                                        'run.googleapis.com/vpc-access-connector': f'{self.subnetwork_name}-func',
                                        'run.googleapis.com/vpc-access-egress': 'private-ranges-only'
                                    }
                                },
                                'spec': {
                                    'timeout_seconds': service['spec']['template']['spec'].get('timeoutSeconds'),
                                    'container_concurrency': service['spec']['template']['spec'].get('containerConcurrency'),
                                    'containers': [
                                        {
                                            'image': container['image'],
                                            'command': container.get('command'),
                                            'args': container.get('args'),
                                            'env': self._extract_container_env(container.get('env', [])),
                                            'resources': container.get('resources'),
                                            'ports': container.get('ports')
                                        } for container in service['spec']['template']['spec'].get('containers', [])
                                    ]
                                }
                            },
                            'traffic': service['spec']['traffic']
                        }
                        primary_services.append(primary_service_info)
                        
                        # Create DR Cloud Run service configuration with '-dr' suffix
                        dr_service_info = {
                            'name': service['metadata']['name'] + '-dr',
                            'template': {
                                'metadata': {
                                    'annotations': {
                                        'autoscaling.knative.dev/maxScale': '1000',
                                        'run.googleapis.com/client-name': 'terraform',
                                        'run.googleapis.com/vpc-access-connector': f'{self.subnetwork_name}-func-dr',
                                        'run.googleapis.com/vpc-access-egress': 'private-ranges-only'
                                    }
                                },
                                'spec': {
                                    'timeout_seconds': service['spec']['template']['spec'].get('timeoutSeconds'),
                                    'container_concurrency': service['spec']['template']['spec'].get('containerConcurrency'),
                                    'containers': [
                                        {
                                            'image': container['image'],
                                            'command': container.get('command'),
                                            'args': container.get('args'),
                                            'env': self._extract_container_env(container.get('env', [])),
                                            'resources': container.get('resources'),
                                            'ports': container.get('ports')
                                        } for container in service['spec']['template']['spec'].get('containers', [])
                                    ]
                                }
                            },
                            'traffic': service['spec']['traffic']
                        }
                        dr_services.append(dr_service_info)
        except Exception as e:
            print(f"Error getting Cloud Run services: {e}")
            raise ValueError(f"Error getting Cloud Run services: {e}")
        return primary_services, dr_services

    def _extract_container_env(self, env_data) -> List[Dict[str, str]]:
        """
        Extract environment variables from container configuration.
        Handles both list and dictionary formats.
        
        Args:
            env_data: Environment data from container config (can be list or dict)
            
        Returns:
            List of environment variable dictionaries
        """
        env_list = []
        
        for env_var in env_data:
            if 'name' in env_var and 'value' in env_var:
                if env_var['name'] not in ['PIVOT_PROXY_HOST', 'EXPORTER_URL']:
                    env_list.append({
                        'name': env_var['name'],
                        'value': env_var['value']
                    })
        return env_list
    
    def get_container_clusters(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discover GKE container clusters for both primary and DR sites.
        
        Uses gcloud CLI to fetch GKE clusters and creates primary/DR configurations.
        DR clusters get '-dr' suffix for easy identification and deployment.
        
        Returns:
            Tuple of (primary_clusters, dr_clusters) lists containing:
            - name: Cluster name (DR version gets '-dr' suffix)
            - subnetwork: Associated subnetwork name (DR version gets '-dr' suffix)
            - default_max_pods_per_node: Maximum pods per node constraint
            - ip_allocation_policy: IP allocation policy configuration
            - logging_service: Logging service configuration
            - monitoring_service: Monitoring service configuration
            - release_channel: Release channel configuration
            - private_cluster_config: Private cluster configuration
            - addons_config: Addons configuration
            - database_encryption: Database encryption configuration
            - cluster_autoscaling: Cluster autoscaling configuration
            - node_pools: Node pool configurations
        """
        primary_clusters = []
        dr_clusters = []
        
        try:
            result = subprocess.run([
                'gcloud', 'container', 'clusters', 'list', 
                '--filter', f"subnetwork = \"{self.subnetwork_name}\"", '--format=json', '--project', self.project_id
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for cluster in json.loads(result.stdout):
                    # Create primary GKE cluster configuration
                    primary_cluster_info = {
                        'name': cluster['name'],
                        'subnetwork': cluster['subnetwork'],
                        'default_max_pods_per_node': cluster['defaultMaxPodsConstraint']['maxPodsPerNode'],
                        'ip_allocation_policy': self._extract_ip_allocation_policy(cluster.get('ipAllocationPolicy'),False),
                        'deletion_protection': cluster['deletionProtection'] if cluster.get('deletionProtection') else True,
                        'logging_service': cluster['loggingService'],
                        'monitoring_service': cluster['monitoringService'],
                        'release_channel': {
                            'channel': cluster.get('releaseChannel').get('channel')
                        } if cluster.get('releaseChannel') else {
                            'channel': 'UNSPECIFIED'
                        },
                        'private_cluster_config': self._extract_private_cluster_config(cluster.get('privateClusterConfig'),False),
                        'addons_config': self._extract_addons_config(cluster.get('addonsConfig')),
                        'database_encryption': self._extract_database_encryption(cluster.get('databaseEncryption')),
                        'cluster_autoscaling': self._extract_cluster_autoscaling(cluster.get('autoscaling')),
                        'node_pools': self._extract_node_pools(cluster.get('nodePools', []),False)
                    }
                    primary_clusters.append(primary_cluster_info)
                    
                    # Create DR GKE cluster configuration with '-dr' suffix
                    dr_cluster_info = {
                        'name': cluster['name'] + '-dr',
                        'subnetwork': cluster['subnetwork'] + '-dr',  # DR subnetwork gets '-dr' suffix
                        'default_max_pods_per_node': cluster['defaultMaxPodsConstraint']['maxPodsPerNode'],
                        'ip_allocation_policy': self._extract_ip_allocation_policy(cluster.get('ipAllocationPolicy'),True),
                        'deletion_protection': False,
                        'logging_service': cluster['loggingService'],
                        'monitoring_service': cluster['monitoringService'],
                        'release_channel': {
                            'channel': cluster.get('releaseChannel').get('channel')
                        } if cluster.get('releaseChannel') else {
                            'channel': 'UNSPECIFIED'
                        },
                        'private_cluster_config': self._extract_private_cluster_config(cluster.get('privateClusterConfig'),True),
                        'addons_config': self._extract_addons_config(cluster.get('addonsConfig')),
                        'database_encryption': self._extract_database_encryption(cluster.get('databaseEncryption')),
                        'cluster_autoscaling': self._extract_cluster_autoscaling(cluster.get('autoscaling')),
                        'node_pools': self._extract_node_pools(cluster.get('nodePools', []),True)
                    }
                    dr_clusters.append(dr_cluster_info)
        except Exception as e:
            print(f"Error getting container clusters: {e}")
            raise ValueError(f"Error getting container clusters: {e}")
        return primary_clusters, dr_clusters

    def _extract_ip_allocation_policy(self, policy: Optional[Dict[str, Any]], is_dr: bool) -> Optional[Dict[str, Any]]:
        """Extract IP allocation policy from cluster config."""
        if not policy:
            return None
        if is_dr:
            return {
                'cluster_secondary_range_name': policy.get('clusterSecondaryRangeName') + '-dr',
                'services_secondary_range_name': policy.get('servicesSecondaryRangeName') + '-dr'
            }
        else:
            return {    
                'cluster_secondary_range_name': policy.get('clusterSecondaryRangeName'),
                'services_secondary_range_name': policy.get('servicesSecondaryRangeName')
        }

    def _extract_private_cluster_config(self, config: Optional[Dict[str, Any]], is_dr: bool) -> Optional[Dict[str, Any]]:
        """Extract private cluster configuration."""
        if not config:
            return None
        if is_dr:
            return {
                'enable_private_nodes': config.get('enablePrivateNodes'),
                'master_ipv4_cidr_block': self.ip_ranges.get('dr', {}).get('gke_master_ip_cidr_range', '')
            }
        else:
            return {
                'enable_private_nodes': config.get('enablePrivateNodes'),
                'master_ipv4_cidr_block': self.ip_ranges.get('primary', {}).get('gke_master_ip_cidr_range', '')
            }

    def _extract_addons_config(self, config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract addons configuration."""
        if not config:
            return None
        return {
            'network_policy_config': {
                'disabled': config.get('networkPolicyConfig', {}).get('disabled')
            } if config.get('networkPolicyConfig') else None,
            'gce_persistent_disk_csi_driver_config': {
                'enabled': config.get('gcePersistentDiskCsiDriverConfig', {}).get('enabled')
            } if config.get('gcePersistentDiskCsiDriverConfig') else None,
            'gcs_fuse_csi_driver_config': {
                'enabled': config.get('gcsFuseCsiDriverConfig', {}).get('enabled')
            } if config.get('gcsFuseCsiDriverConfig') else None
        }

    def _extract_database_encryption(self, config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract database encryption configuration."""
        if not config:
            return None
        return {
            'state': config.get('state'),
        }

    def _extract_cluster_autoscaling(self, config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract cluster autoscaling configuration."""
        if not config:
            return None
        return {
            'autoscaling_profile': config.get('autoscalingProfile')
        }

    def _extract_node_pools(self, node_pools: List[Dict[str, Any]], is_dr: bool) -> List[Dict[str, Any]]:
        """Extract node pool configurations."""
        extracted_pools = []
        for node_pool in node_pools:
            pool_info = {
                'name': node_pool['name'] + '-dr' if is_dr else node_pool['name'],
                # DR node pool initial node count is always 1 for faster deployment
                'initial_node_count': 1 if is_dr or node_pool.get('initialNodeCount') is None else node_pool.get('initialNodeCount'),
                'autoscaling': {
                    'enabled': node_pool.get('autoscaling', {}).get('enabled'),
                    'total_min_node_count': node_pool.get('autoscaling', {}).get('totalMinNodeCount'),
                    'total_max_node_count': node_pool.get('autoscaling', {}).get('totalMaxNodeCount'),
                    'max_node_count': node_pool.get('autoscaling', {}).get('maxNodeCount'),
                    'min_node_count': node_pool.get('autoscaling', {}).get('minNodeCount'),
                    'location_policy': node_pool.get('autoscaling', {}).get('locationPolicy')
                } if 'autoscaling' in node_pool else None,
                'max_pods_constraint': {
                    'max_pods_per_node': node_pool.get('maxPodsConstraint', {}).get('maxPodsPerNode')
                } if 'maxPodsConstraint' in node_pool else None,
                'management': {
                    'auto_repair': node_pool.get('management', {}).get('autoRepair')
                } if 'management' in node_pool else None,
                'upgrade_settings': {
                    'max_surge': node_pool.get('upgradeSettings', {}).get('maxSurge')
                } if 'upgradeSettings' in node_pool else None,
                'node_config': {
                    'machine_type': node_pool.get('config', {}).get('machineType'),
                    'disk_size_gb': node_pool.get('config', {}).get('diskSizeGb'),
                    'disk_type': node_pool.get('config', {}).get('diskType'),
                    'image_type': node_pool.get('config', {}).get('imageType'),
                    'labels': node_pool.get('config', {}).get('labels', {}),
                    'service_account': node_pool.get('config', {}).get('serviceAccount'),
                    'oauth_scopes': node_pool.get('config', {}).get('oauthScopes', []),
                    'shielded_instance_config': node_pool.get('config', {}).get('shieldedInstanceConfig'),
                    'metadata': node_pool.get('config', {}).get('metadata', {}),
                    'linux_node_config': node_pool.get('config', {}).get('linuxNodeConfig')
                }
            }
            extracted_pools.append(pool_info)
        return extracted_pools

    def get_firewall_rules(self, name_regex: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discover firewall rules for both primary and DR sites.
        
        Uses gcloud CLI to fetch firewall rules and creates primary/DR configurations.
        DR rules get '-dr' suffix for easy identification and deployment.
        Supports filtering by name pattern (e.g., '^dpc.*-allow-.*' for DPC rules).
        
        Args:
            name_regex: Optional regex pattern to filter firewall rules by name
            
        Returns:
            Tuple of (primary_rules, dr_rules) lists containing:
            - name: Firewall rule name (DR version gets '-dr' suffix)
            - description: Rule description
            - priority: Rule priority (lower = higher priority)
            - direction: Traffic direction (INGRESS/EGRESS)
            - disabled: Whether rule is disabled
            - source_ranges: Source IP ranges
            - destination_ranges: Destination IP ranges
            - allowed/denied: Protocol and port configurations
        """
        primary_rules = []
        dr_rules = []
        
        try:
            # Use gcloud CLI instead of API client to avoid SSL issues
            result = subprocess.run([
                'gcloud', 'compute', 'firewall-rules', 'list',
                '--project', self.project_id,
                '--filter', f'network="{self.network_name}"',
                '--format', 'json', '--project', self.project_id
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for firewall in json.loads(result.stdout):
                    # Apply regex filtering if specified
                    if name_regex and not re.search(name_regex, firewall['name']):
                        continue
                        
                    # Create primary firewall rule configuration
                    primary_firewall_info = {
                        'name': firewall['name'],
                        'description': firewall.get('description', ''),
                        'priority': firewall.get('priority', 0),
                        'direction': firewall.get('direction', ''),
                        'disabled': firewall.get('disabled', False),
                        'source_ranges': self._get_source_ranges(firewall['name'],False),
                        'destination_ranges': firewall.get('destinationRanges', []),
                        'source_tags': firewall.get('sourceTags', []),
                        'target_tags': [firewall.get('targetTags')[0]],
                        'source_service_accounts': firewall.get('sourceServiceAccounts', []),
                        'target_service_accounts': firewall.get('targetServiceAccounts', []),
                        'allowed': [
                            {
                                'ip_protocol': rule.get('IPProtocol', ''),
                                'ports': rule.get('ports', [])
                            } for rule in firewall.get('allowed', [])
                        ],
                        'denied': [
                            {
                                'ip_protocol': rule.get('IPProtocol', ''),
                                'ports': rule.get('ports', [])
                            } for rule in firewall.get('denied', [])
                        ]
                    }
                    primary_rules.append(primary_firewall_info)
                    
                    # Create DR firewall rule configuration with '-dr' suffix
                    dr_firewall_info = {
                        'name': firewall['name'] + '-dr',
                        'description': firewall.get('description', ''),
                        'priority': firewall.get('priority', 0),
                        'direction': firewall.get('direction', ''),
                        'disabled': firewall.get('disabled', False),
                        'source_ranges': self._get_source_ranges(firewall['name'],True),
                        'destination_ranges': firewall.get('destinationRanges', []),
                        'source_tags': firewall.get('sourceTags', []),
                        'target_tags': [firewall.get('targetTags')[0] + '-dr'],
                        'source_service_accounts': firewall.get('sourceServiceAccounts', []),
                        'target_service_accounts': firewall.get('targetServiceAccounts', []),
                        'allowed': [
                            {
                                'ip_protocol': rule.get('IPProtocol', ''),
                                'ports': rule.get('ports', [])
                            } for rule in firewall.get('allowed', [])
                        ],
                        'denied': [
                            {
                                'ip_protocol': rule.get('IPProtocol', ''),
                                'ports': rule.get('ports', [])
                            } for rule in firewall.get('denied', [])
                        ]
                    }
                    dr_rules.append(dr_firewall_info)
                
        except Exception as e:
            print(f"Error getting firewall rules: {e}")
            raise ValueError(f"Error getting firewall rules: {e}")
        return primary_rules, dr_rules

    def _get_source_ranges(self, name: str, is_dr: bool) -> List[str]:
        """Get source ranges for a firewall rule."""
        if 'allow-gke' in name:
            if is_dr:
                return [self.ip_ranges.get('dr', {}).get('subnet_ip_cidr_range'), self.ip_ranges.get('dr', {}).get('secondary_ip_range_pod'), self.ip_ranges.get('dr', {}).get('secondary_ip_range_svc')]
            else:
                return [self.ip_ranges.get('primary', {}).get('subnet_ip_cidr_range'), self.ip_ranges.get('primary', {}).get('secondary_ip_range_pod'), self.ip_ranges.get('primary', {}).get('secondary_ip_range_svc')]
        elif 'allow-vms' in name:
            if is_dr:
                return [self.ip_ranges.get('dr', {}).get('subnet_ip_cidr_range')]
            else:
                return [self.ip_ranges.get('primary', {}).get('subnet_ip_cidr_range')]
        else:
            return []

    def get_compute_addresses(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discover compute addresses for both primary and DR sites.
        
        Uses gcloud CLI to fetch compute addresses and creates primary/DR configurations.
        DR addresses get '-dr' suffix for easy identification and deployment.
        Addresses are typically used for load balancers, VPN gateways, and other
        network services requiring static IP addresses.
        
        Returns:
            Tuple of (primary_addresses, dr_addresses) lists containing:
            - name: Address name (DR version gets '-dr' suffix)
            - description: Address description
            - address_type: Type (INTERNAL/EXTERNAL)
            - subnetwork: Associated subnetwork name (DR version gets '-dr' suffix)
            - purpose: Address purpose (GCE_ENDPOINT, SHARED_LOADBALANCER_VIP, etc.)
            - ip_version: IP version (IPV4/IPV6)
            - network_tier: Network tier (PREMIUM/STANDARD)
        """
        primary_addresses = []
        dr_addresses = []
        
        subnetwork_filter = f"subnetwork = \"https://www.googleapis.com/compute/v1/projects/{self.project_id}/regions/{self.region}/subnetworks/{self.subnetwork_name}\""
        try:
            # Use gcloud CLI instead of API client to avoid SSL issues
            result = subprocess.run([
                'gcloud', 'compute', 'addresses', 'list',
                '--project', self.project_id,
                '--regions', self.region,
                '--filter', subnetwork_filter,
                '--format', 'json', '--project', self.project_id
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for address in json.loads(result.stdout):
                    # Create primary compute address configuration
                    primary_address_info = {
                        'name': address['name'],
                        'description': address.get('description', ''),
                        'address_type': address.get('addressType', ''),
                        'purpose': address.get('purpose', ''),
                        'ip_version': address.get('ipVersion'),
                        'network_tier': address.get('networkTier'),
                        'subnetwork': address.get('subnetwork', '').rsplit('/', 1)[-1] if address.get('subnetwork') else None
                    }
                    primary_addresses.append(primary_address_info)
                    
                    # Create DR compute address configuration with '-dr' suffix
                    dr_address_info = {
                        'name': address['name'] + '-dr',
                        'description': address.get('description', ''),
                        'address_type': address.get('addressType', ''),
                        'purpose': address.get('purpose', ''),
                        'ip_version': address.get('ipVersion'),
                        'network_tier': address.get('networkTier'),
                        'subnetwork': address.get('subnetwork', '').rsplit('/', 1)[-1] + '-dr' if address.get('subnetwork') else None
                    }
                    dr_addresses.append(dr_address_info)
                
        except Exception as e:
            print(f"Error getting compute addresses: {e}")
            raise ValueError(f"Error getting compute addresses: {e}")   
        return primary_addresses, dr_addresses

    def get_vpc_access_connectors(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get VPC Access Connectors for the specified network.
        
        Returns:
            Tuple of (primary_connectors, dr_connectors) lists containing:
            - name: Connector name (DR version gets '-dr' suffix)
            - min_throughput: Minimum throughput
            - max_throughput: Maximum throughput
            - machine_type: Machine type
            - subnet: Subnet configuration
        """
        connectors = []
        connectors_dr = []
        try:
            # Use gcloud CLI to get global addresses since the API client doesn't have the method
            result = subprocess.run([
                'gcloud', 'compute', 'networks', 'vpc-access', 'connectors', 'list', 
                '--region', self.region, '--format=json', '--project', self.project_id,
                '--filter', f'network="{self.network_name}"'
            ], capture_output=True, text=True, check=True)

            if result.returncode == 0:
                for connector in json.loads(result.stdout):
                    connector_info = {
                        'name': connector['name'].rsplit('/', 1)[-1],
                        'min_throughput': connector['minThroughput'],
                        'max_throughput': connector['maxThroughput'],
                        'machine_type': connector['machineType'],
                        'subnet': {
                            'name': connector['subnet']['name']
                        } if connector['subnet'] else {
                            'name': connector['name'].rsplit('/', 1)[-1]
                        }
                    }
                    connectors.append(connector_info)
                    dr_connector_info = {
                        'name': connector['name'].rsplit('/', 1)[-1] + '-dr',
                        'min_throughput': connector['minThroughput'],
                        'max_throughput': connector['maxThroughput'],
                        'machine_type': connector['machineType'],
                        'subnet': {
                            'name': connector['subnet']['name'] + '-dr'
                        } if connector['subnet'] else {
                            'name': connector['name'].rsplit('/', 1)[-1] + '-dr'
                        }
                    }
                    connectors_dr.append(dr_connector_info) 
        except Exception as e:
            print(f"Error getting VPC Access Connectors: {e}")
            raise ValueError(f"Error getting VPC Access Connectors: {e}")
        return connectors, connectors_dr

    def get_redis_instances(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discover Redis instances for both primary and DR sites.
        
        Uses gcloud CLI to fetch Redis instances and creates primary/DR configurations.
        DR instances get '-dr' suffix for easy identification and deployment.
        
        Returns:
            Tuple of (primary_instances, dr_instances) lists containing:
            - name: Instance name (DR version gets '-dr' suffix)
            - display_name: Display name
            - redis_version: Redis version
            - tier: Instance tier
            - memory_size_gb: Memory size in GB
            - port: Redis port
            - connect_mode: Connection mode
            - auth_enabled: Authentication enabled flag
            - transit_encryption_mode: Transit encryption mode
            - redis_configs: Redis configuration
            - replica_count: Number of replicas
            - read_replicas_mode: Read replicas mode
            - persistence_config: Persistence configuration
        """
        primary_instances = []
        dr_instances = []
        
        try:
            # Use gcloud CLI to get Redis instances since the API client requires location
            result = subprocess.run([
                'gcloud', 'redis', 'instances', 'list', 
                '--region', self.region, '--format=json', '--project', self.project_id,
                '--filter', f'authorizedNetwork : projects/{self.project_id}/global/networks/{self.network_name}'
            ], capture_output=True, text=True, check=True)

            if result.returncode == 0:
                for instance in json.loads(result.stdout):
                    # Create primary Redis instance configuration
                    primary_instance_info = {
                        'name': instance['name'].rsplit('/', 1)[-1],
                        'display_name': instance.get('displayName', ''),
                        'redis_version': instance.get('redisVersion', ''),
                        'tier': instance.get('tier', ''),
                        'memory_size_gb': instance.get('memorySizeGb', 0),
                        'port': instance.get('port', 6379),
                        'connect_mode': instance.get('connectMode', ''),
                        'auth_enabled': instance.get('authEnabled', False),
                        'transit_encryption_mode': instance.get('transitEncryptionMode', ''),
                        'redis_configs': instance.get('redisConfigs', {}),
                        'replica_count': instance.get('replicaCount', 0),
                        'read_replicas_mode': instance.get('readReplicasMode', ''),
                        'persistence_config': {
                            'persistence_mode': instance.get('persistenceConfig', {}).get('persistenceMode', '')
                        } if instance.get('persistenceConfig') else None
                    }
                    primary_instances.append(primary_instance_info)
                    
                    # Create DR Redis instance configuration with '-dr' suffix
                    dr_instance_info = {
                        'name': instance['name'].rsplit('/', 1)[-1] + '-dr',
                        'display_name': instance.get('displayName', '') + '-dr',
                        'redis_version': instance.get('redisVersion', ''),
                        'tier': instance.get('tier', ''),
                        'memory_size_gb': instance.get('memorySizeGb', 0),
                        'port': instance.get('port', 6379),
                        'connect_mode': instance.get('connectMode', ''),
                        'auth_enabled': instance.get('authEnabled', False),
                        'transit_encryption_mode': instance.get('transitEncryptionMode', ''),
                        'redis_configs': instance.get('redisConfigs', {}),
                        'replica_count': instance.get('replicaCount', 0),
                        'read_replicas_mode': instance.get('readReplicasMode', ''),
                        'persistence_config': {
                            'persistence_mode': instance.get('persistenceConfig', {}).get('persistenceMode', '')
                        } if instance.get('persistenceConfig') else None
                    }
                    dr_instances.append(dr_instance_info)
        except Exception as e:
            print(f"Error getting Redis instances: {e}")
            raise ValueError(f"Error getting Redis instances: {e}")
        return primary_instances, dr_instances

    def get_sql_databases(self, instance_name: str) -> List[Dict[str, Any]]:
        """
        Get databases for a specific SQL instance.
        
        Args:
            instance_name: The name of the SQL instance
            
        Returns:
            List of database dictionaries
        """
        databases = []
        
        try:
            # Use gcloud CLI to get databases for the instance
            result = subprocess.run([
                'gcloud', 'sql', 'databases', 'list', 
                '--instance', instance_name,
                '--format=json', '--project', self.project_id
            ], capture_output=True, text=True, check=True)

            if result.returncode == 0:
                for database in json.loads(result.stdout):
                    if database.get('name') != 'postgres':
                        databases.append(database.get('name'))
        except Exception as e:
            print(f"Error getting databases for instance {instance_name}: {e}")
            # Don't raise error, just return empty list
            return []
        return databases

    def get_sql_postgres_instances(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Discover Cloud SQL PostgreSQL instances for both primary and DR sites.
        
        Uses gcloud CLI to fetch PostgreSQL instances and creates primary/DR configurations.
        DR instances get '-dr' suffix for easy identification and deployment.
        
        Returns:
            Tuple of (primary_instances, dr_instances) lists containing:
            - name: Instance name (DR version gets '-dr' suffix)
            - database_version: PostgreSQL version
            - instance_type: Instance type
            - machine_type: Machine type/tier
            - database_flags: Database flags configuration
            - backup_configuration: Backup configuration
            - ip_configuration: IP configuration (DR private network gets '-dr' suffix)
            - availability_type: Availability type
            - data_disk_size_gb: Data disk size
            - data_disk_type: Data disk type
            - databases: List of databases
        """
        primary_instances = []
        dr_instances = []
        
        try:
            # Use gcloud CLI to get SQL instances
            result = subprocess.run([
                'gcloud', 'sql', 'instances', 'list', 
                '--format=json', '--project', self.project_id
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for instance in json.loads(result.stdout):
                    # Check if this is a PostgreSQL instance
                    if instance.get('databaseVersion', '').startswith('POSTGRES'):
                        # Check if the instance is in the specified network
                        # SQL instances can be connected to VPC through private services access
                        # We'll check if the instance has any network configuration that matches our network
                        network_info = instance.get('settings', {}).get('ipConfiguration', {})
                        
                        # Check if the instance has private IP configuration that might be in our network
                        if network_info.get('privateNetwork'):
                            private_network = network_info['privateNetwork']
                            if f"/networks/{self.network_name}" in private_network:
                                instance_name = instance['name'].rsplit('/', 1)[-1]
                                
                                # Get databases for this instance
                                databases = self.get_sql_databases(instance_name)
                                
                                # Create primary PostgreSQL instance configuration
                                primary_instance_info = {
                                    'name': instance_name,
                                    'database_version': instance.get('databaseVersion', ''),
                                    'instance_type': instance.get('instanceType', ''),
                                    'machine_type': instance.get('settings', {}).get('tier', ''),
                                    'database_flags': instance.get('settings', {}).get('databaseFlags', []),
                                    'deletion_protection':  True,
                                    'backup_configuration': {
                                        'enabled': instance.get('settings', {}).get('backupConfiguration', {}).get('enabled', False),
                                        'binary_log_enabled': instance.get('settings', {}).get('backupConfiguration', {}).get('binaryLoggingEnabled', False)
                                    } if instance.get('settings', {}).get('backupConfiguration') else None,
                                    'ip_configuration': {
                                        'ipv4_enabled': instance.get('settings', {}).get('ipConfiguration', {}).get('ipv4Enabled', False)
                                    } if instance.get('settings', {}).get('ipConfiguration') else None,
                                    'availability_type': instance.get('settings', {}).get('availabilityType', ''),
                                    'data_disk_size_gb': instance.get('settings', {}).get('dataDiskSizeGb', 0),
                                    'data_disk_type': instance.get('settings', {}).get('dataDiskType', ''),
                                    'databases': databases
                                }
                                primary_instances.append(primary_instance_info)
                                
                                # Create DR PostgreSQL instance configuration with '-dr' suffix
                                dr_instance_info = {
                                    'name': instance_name + '-dr',
                                    'database_version': instance.get('databaseVersion', ''),
                                    'instance_type': instance.get('instanceType', ''),
                                    'machine_type': instance.get('settings', {}).get('tier', ''),
                                    'database_flags': instance.get('settings', {}).get('databaseFlags', []),
                                    'deletion_protection': False,
                                    'backup_configuration': {
                                        'enabled': instance.get('settings', {}).get('backupConfiguration', {}).get('enabled', False),
                                        'binary_log_enabled': instance.get('settings', {}).get('backupConfiguration', {}).get('binaryLoggingEnabled', False)
                                    } if instance.get('settings', {}).get('backupConfiguration') else None,
                                    'ip_configuration': {
                                        'ipv4_enabled': instance.get('settings', {}).get('ipConfiguration', {}).get('ipv4Enabled', False)
                                    } if instance.get('settings', {}).get('ipConfiguration') else None,
                                    'availability_type': instance.get('settings', {}).get('availabilityType', ''),
                                    'data_disk_size_gb': instance.get('settings', {}).get('dataDiskSizeGb', 0),
                                    'data_disk_type': instance.get('settings', {}).get('dataDiskType', ''),
                                    'databases': databases
                                }
                                dr_instances.append(dr_instance_info)
        except Exception as e:
            print(f"Error getting PostgreSQL instances: {e}")
            raise ValueError(f"Error getting PostgreSQL instances: {e}")
        return primary_instances, dr_instances

    def get_all_resources(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Discover all GCP resources for both primary and DR sites.
        
        Orchestrates the discovery of all resource types and creates comprehensive
        configurations for both primary and disaster recovery deployments.
        
        Returns:
            Tuple of (primary_resources, dr_resources) dictionaries containing:
            - compute_network: VPC network configuration
            - compute_subnetworks: Subnetwork configurations with IP ranges
            - nat_routers: NAT router configurations
            - dataproc_cluster: DataProc cluster details
            - container_clusters: GKE cluster configurations
            - cloud_functions: Cloud Functions configurations
            - cloud_run_services: Cloud Run service configurations
            - firewall_rules: Firewall rule configurations
            - compute_addresses: Static IP address configurations
            - redis_instances: Redis cache configurations
            - sql_postgres_instances: Cloud SQL PostgreSQL configurations
        """
        print(f"Fetching all GCP resources for project: {self.project_id}")
        
        all_resources = {
            'timestamp': datetime.datetime.now().isoformat(),
            'project': self.project_id,
            'region': self.region,
            'compute_network': {},
            'compute_subnetworks': [],
            'nat_routers': [],
            'vpc_access_connectors': [],
            'dataproc_cluster': {},
            'container_clusters': [],
            'cloud_functions': [],
            'cloud_run_services': [],
            'firewall_rules': [],
            'compute_addresses': [],
            'redis_instances': [],
            'sql_postgres_instances': []
        }

        all_resources_dr = {
            'timestamp': datetime.datetime.now().isoformat(),
            'project': self.project_id,
            'region': self.dr_region,
            'compute_network': {},
            'compute_subnetworks': [],
            'nat_routers': [],
            'vpc_access_connectors': [],
            'dataproc_cluster': {},
            'container_clusters': [],
            'cloud_functions': [],
            'cloud_run_services': [],
            'firewall_rules': [],
            'compute_addresses': [],
            'redis_instances': [],
            'sql_postgres_instances': []
        }
        
        try:
            # Initialize compute network configuration for both sites
            print("Added Compute Network: ", self.network_name)
            all_resources['compute_network'] = {
                'name': self.network_name
            }
            all_resources_dr['compute_network'] = {
                'name': self.network_name
            }
            
            # Discover subnetworks for both primary and DR sites
            print("Fetching Compute Subnetworks...")
            all_resources['compute_subnetworks'], all_resources_dr['compute_subnetworks'] = self.get_compute_subnetworks()
            print(f"Found {len(all_resources['compute_subnetworks'])} Compute Subnetworks")
            
            # Discover NAT routers for both primary and DR sites
            print("Fetching NAT Routers...")
            all_resources['nat_routers'], all_resources_dr['nat_routers'] = self.get_nat_routers()
            print(f"Found {len(all_resources['nat_routers'])} NAT Routers")
            
            # Discover DataProc cluster configuration for both primary and DR sites
            print("Fetching DataProc Clusters...")
            all_resources['dataproc_cluster'], all_resources_dr['dataproc_cluster'] = self.get_dataproc_clusters()
            print(f"Found 1 DataProc Cluster")
            
            # Discover Cloud Functions for both primary and DR sites
            print("Fetching Cloud Functions...")
            all_resources['cloud_functions'], all_resources_dr['cloud_functions'] = self.get_cloudfunctions()
            print(f"Found {len(all_resources['cloud_functions'])} Cloud Functions")

            # Discover Cloud Run services for both primary and DR sites
            print("Fetching Cloud Run Services...")
            all_resources['cloud_run_services'], all_resources_dr['cloud_run_services'] = self.get_cloudrun()
            print(f"Found {len(all_resources['cloud_run_services'])} Cloud Run Services")
            
            # Discover firewall rules for both primary and DR sites (filtered by DPC pattern)
            print("Fetching Firewall Rules...")
            all_resources['firewall_rules'], all_resources_dr['firewall_rules'] = self.get_firewall_rules('^dpc.*-allow-.*')
            print(f"Found {len(all_resources['firewall_rules'])} Firewall Rules")
            
            # Discover compute addresses for both primary and DR sites
            print("Fetching Compute Addresses...")
            all_resources['compute_addresses'], all_resources_dr['compute_addresses'] = self.get_compute_addresses()
            print(f"Found {len(all_resources['compute_addresses'])} Compute Addresses")
            
            # Discover GKE container clusters for both primary and DR sites
            print("Fetching Container Clusters...")
            all_resources['container_clusters'], all_resources_dr['container_clusters'] = self.get_container_clusters()
            print(f"Found {len(all_resources['container_clusters'])} Container Clusters")
            
            # Discover Redis cache instances for both primary and DR sites
            print("Fetching Redis Instances...")
            all_resources['redis_instances'], all_resources_dr['redis_instances'] = self.get_redis_instances()
            print(f"Found {len(all_resources['redis_instances'])} Redis Instances")
            
            # Discover Cloud SQL PostgreSQL instances for both primary and DR sites
            print("Fetching PostgreSQL Instances...")
            all_resources['sql_postgres_instances'], all_resources_dr['sql_postgres_instances'] = self.get_sql_postgres_instances()
            print(f"Found {len(all_resources['sql_postgres_instances'])} PostgreSQL Instances")
            
            # Note: VPC Access Connectors are commented out for now
            print("Fetching VPC Access Connectors...")
            all_resources['vpc_access_connectors'], all_resources_dr['vpc_access_connectors'] = self.get_vpc_access_connectors()
            print(f"Found {len(all_resources['vpc_access_connectors'])} VPC Access Connectors")

        except Exception as e:
            print(f"Error fetching all resources: {e}")
            raise ValueError(f"Error fetching all resources: {e}")
        return all_resources, all_resources_dr


def main():
    """
    Main function for GCP resource discovery and tfvars generation.
    
    Parses command line arguments and generates comprehensive resource reports
    for specified environments and clusters. Creates both primary and DR
    configuration files for multi-site deployments.
    
    Usage:
        python3 gcp_resource_reader.py --environment stg --cluster r1-rai
        
    Output:
        - Primary: ./configs/{environment}/{cluster}.tfvars.json
        - DR: ./configs/{environment}/{cluster}-dr.tfvars.json
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Read Google Cloud Resource Properties')
    parser.add_argument('--environment', choices=[
        'stg','prod-us','prod-eu','prod-asia'
    ], help='Mlisa environment')
    parser.add_argument('--cluster', choices=[
        'rai','r1-rai'
    ], default='r1-rai', help='Cluster type')
    
    args = parser.parse_args()
    
    try:
        # Initialize the resource reader
        print("Initializing GCP Resource Reader...")
        
        # Load configuration from JSON file
        with open('./configs/config.json') as config_file:
            config_data = json.load(config_file)
        
        reader = GCPResourceReader(
            project_id=config_data[args.environment]['project_id'], 
            network_name=config_data[args.environment][args.cluster]['vpc'],
            region=config_data[args.environment]['region'],
            dr_region=config_data[args.environment]['dr_region'],
            ip_ranges=config_data[args.environment][args.cluster]['ip_ranges'] 
        )
        print(f"Connected to project: {reader.project_id}")
            
        # Get all resources
        resources, resources_dr = reader.get_all_resources()
        
        # Save primary resources to JSON file
        output_filename = f'./configs/{args.environment}/{args.cluster}.tfvars.json'
        with open(output_filename, 'w') as f:
            json.dump(resources, f, indent=2)
        print(f"Primary resources saved to: {output_filename}")
        
        # Save DR resources to JSON file
        output_filename_dr = f'./configs/{args.environment}/{args.cluster}-dr.tfvars.json'
        with open(output_filename_dr, 'w') as f:
            json.dump(resources_dr, f, indent=2)
        print(f"DR resources saved to: {output_filename_dr}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()