#!/usr/bin/env python3
"""
Google Cloud Resource Properties Reader

This script reads properties of various Google Cloud resources:
- Compute Network
- Compute Subnetwork
- Cloud Functions
- Cloud Run
- Cloud VPC Access Connector
- Compute Instance
- DataProc Cluster
- Cloud Container Cluster
- Cloud Container Node Pool
- Firewall Rules
- Compute Addresses
- Redis Instances
- Cloud SQL PostgreSQL Instances
- GCS Buckets

The script filters resources based on a specific VPC network and subnetwork.
"""

import json
import subprocess
import datetime
import re
from typing import Dict, List, Any, Optional, Tuple
from google.cloud import compute_v1
from google.cloud import functions_v1
from google.cloud import run_v2
from google.cloud import container_v1
from google.cloud import redis_v1
from google.cloud import storage
from google.auth import default


class GCPResourceReader:
    """
    Class to read properties of various Google Cloud resources.
    
    This class provides methods to fetch and filter GCP resources based on
    project ID, network name, and region. It supports reading compute resources,
    container clusters, cloud functions, Redis instances, PostgreSQL instances, GCS buckets, and more.
    """
    
    def __init__(self, project_id: Optional[str] = None, 
                 network_name: Optional[str] = None, 
                 region: Optional[str] = None,
                 mlisa_cluster: Optional[str] = None):
        """
        Initialize the GCP Resource Reader.
        
        Args:
            project_id: Google Cloud project ID. If None, will try to get from environment
            network_name: Name of the VPC network to filter resources
            region: GCP region for regional resources
        """
        self.project_id = project_id
        self.network_name = network_name
        self.region = region
        self.mlisa_cluster = mlisa_cluster
        self.subnetwork_name = 'default'
        
        # Get default credentials
        self.credentials, _ = default()
        
        # Validate project and network
        self._check_project_id_and_network_name()

        # Initialize GCP API clients
        self._initialize_clients()
        
        # Construct network filter for API calls
        self.network_filter = f"network = \"https://www.googleapis.com/compute/v1/projects/{self.project_id}/global/networks/{self.network_name}\""

    def _initialize_clients(self):
        """Initialize all GCP API clients."""
        self.compute_client = compute_v1.NetworksClient()
        self.subnetworks_client = compute_v1.SubnetworksClient()
        self.instances_client = compute_v1.InstancesClient()
        self.routers_client = compute_v1.RoutersClient()
        self.functions_client = functions_v1.CloudFunctionsServiceClient()
        self.run_client = run_v2.ServicesClient()
        self.container_client = container_v1.ClusterManagerClient()
        self.firewalls_client = compute_v1.FirewallsClient()
        self.addresses_client = compute_v1.AddressesClient()
        self.redis_client = redis_v1.CloudRedisClient()
        self.storage_client = storage.Client()

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
                subprocess.run(['gcloud', 'config', 'set', 'project', self.project_id], check=True)
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
    
    def get_compute_subnetworks(self) -> List[Dict[str, Any]]:
        """
        Get all Compute Subnetworks in the project, separated by type.
        
        Returns:
            List of Compute Subnetwork configurations
        """
        subnetworks = []
        
        try:
            request = compute_v1.ListSubnetworksRequest(
                project=self.project_id,
                region=self.region,
                filter=self.network_filter
            )
            page_result = self.subnetworks_client.list(request=request)
            
            for subnetwork in page_result:
                if subnetwork.secondary_ip_ranges:
                    self.subnetwork_name = subnetwork.name
                subnetwork_info = {
                    'name': subnetwork.name,
                    'description': subnetwork.description,
                    'network': subnetwork.network.rsplit('/', 1)[-1],
                    'ip_cidr_range': subnetwork.ip_cidr_range,
                    'gateway_address': subnetwork.gateway_address,
                    'private_ip_google_access': subnetwork.private_ip_google_access,
                    'secondary_ip_range': [
                        {
                            'name': range.range_name,
                            'ip_cidr_range': range.ip_cidr_range
                        } for range in subnetwork.secondary_ip_ranges
                    ] if subnetwork.secondary_ip_ranges else []
                }
                subnetworks.append(subnetwork_info)
        except Exception as e:
            print(f"Error getting compute subnetworks: {e}")
            raise ValueError(f"Error getting compute subnetworks: {e}")
            
        return subnetworks
    
    def get_nat_routers(self) -> List[Dict[str, Any]]:
        """
        Get all NAT routers in the project.
        
        Returns:
            List of NAT router configurations
        """
        routers = {}    
        
        try:
            request = compute_v1.ListRoutersRequest(
                project=self.project_id,
                region=self.region,
                filter=self.network_filter
            )
            page_result = self.routers_client.list(request=request)
            
            for router in page_result:
                router_info = {
                    'name': router.name,
                    'description': router.description,
                    'network': router.network.rsplit('/', 1)[-1],
                    'nat':
                    {
                        'name': router.nats[0].name,
                        'nat_ip_allocate_option': router.nats[0].nat_ip_allocate_option.name if hasattr(router.nats[0].nat_ip_allocate_option, 'name') else str(router.nats[0].nat_ip_allocate_option),
                        'source_subnetwork_ip_ranges_to_nat': router.nats[0].source_subnetwork_ip_ranges_to_nat.name if hasattr(router.nats[0].source_subnetwork_ip_ranges_to_nat, 'name') else str(router.nats[0].source_subnetwork_ip_ranges_to_nat),
                        'max_ports_per_vm': router.nats[0].max_ports_per_vm,
                        'log_config': {
                            'enable': router.nats[0].log_config.enable,
                            'filter': router.nats[0].log_config.filter.name if hasattr(router.nats[0].log_config.filter, 'name') else str(router.nats[0].log_config.filter)
                        } if router.nats[0].log_config else None,
                    }if len(router.nats) > 0 else []
                }
                routers[router.name] = router_info
                
        except Exception as e:
            print(f"Error getting NAT routers: {e}")
            raise ValueError(f"Error getting NAT routers: {e}")
        return routers

    def _extract_dataproc_labels(self, labels_data) -> Dict[str, str]:
        """
        Extract and filter labels from DataProc cluster configuration.
        Handles different label formats and filters out unwanted labels.
        
        Args:
            labels_data: Labels data from cluster config (can be list or dict)
            
        Returns:
            Dictionary of filtered labels
        """
        labels = {}
        
        if not labels_data:
            return labels
            
        if isinstance(labels_data, list):
            # Labels as list of objects with key/value
            for label in labels_data:
                if isinstance(label, dict) and 'key' in label and 'value' in label:
                    if label['key'] != 'goog-dataproc-cluster-uuid':
                        labels[label['key']] = label['value']
        elif isinstance(labels_data, dict):
            # Labels as direct key-value dictionary
            labels = {k: v for k, v in labels_data.items() if k != 'goog-dataproc-cluster-uuid'}
        else:
            print(f"Unexpected labels format: {type(labels_data)}")
            
        return labels

    def get_dataproc_clusters(self) -> Dict[str, Any]:
        """
        Get the first DataProc cluster in the project that uses the specified subnetwork.
        
        Returns:
            Dictionary containing the first DataProc cluster configuration or empty dict if none found
        """
        cluster_info = {}
        
        try:
            result = subprocess.run([
                'gcloud', 'dataproc', 'clusters', 'list', 
                '--region', self.region, '--format=json'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for cluster in json.loads(result.stdout):
                    # Filter clusters by subnetwork
                    cluster_subnetwork = cluster['config']['gceClusterConfig']['subnetworkUri'].rsplit('/', 1)[-1]
                    if cluster_subnetwork == self.subnetwork_name:
                        cluster_info = {
                            'cluster_name': cluster['clusterName'],
                            'labels': self._extract_dataproc_labels(cluster['labels']),
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
                        # Return only the first cluster found
                        break
        except Exception as e:
            print(f"Error getting DataProc clusters: {e}")
            raise ValueError(f"Error getting DataProc clusters: {e}")
        return cluster_info

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
    
    def get_cloudfunctions(self) -> List[Dict[str, Any]]:
        """
        Get all Cloud Functions in the project that use the VPC connector.
        
        Returns:
            List of Cloud Function configurations
        """
        functions = []
        vpc_connector_filter = f"vpcConnector = \"projects/{self.project_id}/locations/{self.region}/connectors/{self.subnetwork_name}-func\""
        
        try:
            result = subprocess.run([
                'gcloud', 'functions', 'list', '--format=json', '--filter', vpc_connector_filter
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for function in json.loads(result.stdout):
                    function_info = {
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
                    functions.append(function_info)
        except Exception as e:
            print(f"Error getting Cloud Functions: {e}")
            raise ValueError(f"Error getting Cloud Functions: {e}")
        return functions
    
    def get_cloudrun(self) -> List[Dict[str, Any]]:
        """
        Get all Cloud Run services in the project that use the VPC connector.
        
        Returns:
            List of Cloud Run service configurations
        """
        services = []
        
        try:
            result = subprocess.run([
                'gcloud', 'run', 'services', 'list', '--format=json'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for service in json.loads(result.stdout):
                    # Filter services by VPC connector annotation
                    annotations = service['spec']['template']['metadata'].get('annotations', {})
                    vpc_connector = annotations.get('run.googleapis.com/vpc-access-connector')
                    
                    if vpc_connector == f'{self.subnetwork_name}-func':
                        service_info = {
                            'name': service['metadata']['name'],
                            'template': {
                                'metadata': {
                                    'annotations': annotations
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
                        services.append(service_info)
        except Exception as e:
            print(f"Error getting Cloud Run services: {e}")
            raise ValueError(f"Error getting Cloud Run services: {e}")
        return services

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
    
    def get_container_clusters(self) -> List[Dict[str, Any]]:
        """
        Get all GKE clusters in the project that use the specified subnetwork.
        
        Returns:
            List of GKE cluster configurations
        """
        clusters = []
        
        try:
            result = subprocess.run([
                'gcloud', 'container', 'clusters', 'list', 
                '--filter', f"subnetwork = \"{self.subnetwork_name}\"", '--format=json'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for cluster in json.loads(result.stdout):
                    cluster_info = {
                        'name': cluster['name'],
                        'network': cluster['network'],
                        'subnetwork': cluster['subnetwork'],
                        'default_max_pods_per_node': cluster['defaultMaxPodsConstraint']['maxPodsPerNode'],
                        'ip_allocation_policy': self._extract_ip_allocation_policy(cluster.get('ipAllocationPolicy')),
                        'logging_service': cluster['loggingService'],
                        'monitoring_service': cluster['monitoringService'],
                        'release_channel': {
                            'channel': cluster.get('releaseChannel').get('channel')
                        } if cluster.get('releaseChannel') else {
                            'channel': 'UNSPECIFIED'
                        },
                        'private_cluster_config': self._extract_private_cluster_config(cluster.get('privateClusterConfig')),
                        'addons_config': self._extract_addons_config(cluster.get('addonsConfig')),
                        'database_encryption': self._extract_database_encryption(cluster.get('databaseEncryption')),
                        'cluster_autoscaling': self._extract_cluster_autoscaling(cluster.get('autoscaling')),
                        'node_pools': self._extract_node_pools(cluster.get('nodePools', []))
                    }
                    clusters.append(cluster_info)
        except Exception as e:
            print(f"Error getting container clusters: {e}")
            raise ValueError(f"Error getting container clusters: {e}")
        return clusters

    def _extract_ip_allocation_policy(self, policy: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract IP allocation policy from cluster config."""
        if not policy:
            return None
        return {
            'cluster_secondary_range_name': policy.get('clusterSecondaryRangeName'),
            'services_secondary_range_name': policy.get('servicesSecondaryRangeName')
        }

    def _extract_private_cluster_config(self, config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract private cluster configuration."""
        if not config:
            return None
        return {
            'enable_private_nodes': config.get('enablePrivateNodes'),
            'master_ipv4_cidr_block': config.get('masterIpv4CidrBlock')
        }

    def _extract_addons_config(self, config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract addons configuration."""
        if not config:
            return None
        return {
            'kubernetes_dashboard': {
                'disabled': config.get('kubernetesDashboard', {}).get('disabled')
            } if config.get('kubernetesDashboard') else None,
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

    def _extract_node_pools(self, node_pools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract node pool configurations."""
        extracted_pools = []
        for node_pool in node_pools:
            pool_info = {
                'name': node_pool['name'],
                'initial_node_count': node_pool.get('initialNodeCount') if node_pool.get('initialNodeCount') else 1,
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

    def get_firewall_rules(self, name_regex: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get firewall rules for the specified network with optional name regex filtering.
        
        Args:
            name_regex: Optional regex pattern to filter firewall rules by name
            
        Returns:
            List of firewall rule dictionaries
        """
        firewall_rules = []
        
        try:
            request = compute_v1.ListFirewallsRequest(
                project=self.project_id,
                filter=self.network_filter
            )
            page_result = self.firewalls_client.list(request=request)
            
            for firewall in page_result:
                # Apply regex filtering if specified
                if name_regex and not re.search(name_regex, firewall.name):
                    continue
                    
                firewall_info = {
                    'name': firewall.name,
                    'description': firewall.description,
                    'network': firewall.network.rsplit('/', 1)[-1],
                    'priority': firewall.priority,
                    'direction': firewall.direction.name if hasattr(firewall.direction, 'name') else str(firewall.direction),
                    'disabled': firewall.disabled,
                    'source_ranges': list(firewall.source_ranges) if firewall.source_ranges else [],
                    'destination_ranges': list(firewall.destination_ranges) if firewall.destination_ranges else [],
                    'source_tags': list(firewall.source_tags) if firewall.source_tags else [],
                    'target_tags': list(firewall.target_tags) if firewall.target_tags else [],
                    'source_service_accounts': list(firewall.source_service_accounts) if firewall.source_service_accounts else [],
                    'target_service_accounts': list(firewall.target_service_accounts) if firewall.target_service_accounts else [],
                    'allowed': [
                        {
                            'ip_protocol': rule.I_p_protocol,
                            'ports': list(rule.ports) if rule.ports else []
                        } for rule in firewall.allowed
                    ] if firewall.allowed else [],
                    'denied': [
                        {
                            'ip_protocol': rule.I_p_protocol,
                            'ports': list(rule.ports) if rule.ports else []
                        } for rule in firewall.denied
                    ] if firewall.denied else []
                }
                firewall_rules.append(firewall_info)
                
        except Exception as e:
            print(f"Error getting firewall rules: {e}")
            raise ValueError(f"Error getting firewall rules: {e}")
        return firewall_rules

    def get_compute_addresses(self) -> List[Dict[str, Any]]:
        """
        Get compute addresses for the specified subnetwork.
        
        Returns:
            List of compute address dictionaries
        """
        addresses = []
        
        try:
            # Build filter for subnetwork
            subnetwork_filter = f"subnetwork = \"https://www.googleapis.com/compute/v1/projects/{self.project_id}/regions/{self.region}/subnetworks/{self.subnetwork_name}\""
            
            request = compute_v1.ListAddressesRequest(
                project=self.project_id,
                region=self.region,
                filter=subnetwork_filter
            )
            page_result = self.addresses_client.list(request=request)
            
            for address in page_result:
                address_info = {
                    'name': address.name,
                    'description': address.description,
                    'address_type': address.address_type.name if hasattr(address.address_type, 'name') else str(address.address_type),
                    'subnetwork': address.subnetwork.rsplit('/', 1)[-1],
                    'network_tier': address.network_tier.name if hasattr(address.network_tier, 'name') else str(address.network_tier),
                    'purpose': address.purpose.name if hasattr(address.purpose, 'name') else str(address.purpose),
                    'ip_version': address.ip_version.name if hasattr(address.ip_version, 'name') else str(address.ip_version)
                }
                addresses.append(address_info)
                
        except Exception as e:
            print(f"Error getting compute addresses: {e}")
            raise ValueError(f"Error getting compute addresses: {e}")   
        return addresses

    def get_global_compute_addresses(self) -> List[Dict[str, Any]]:
        """
        Get global compute addresses for the specified network.
        
        Returns:
            List of global compute address dictionaries
        """
        addresses = []
        
        try:
            # Use gcloud CLI to get global addresses since the API client doesn't have the method
            result = subprocess.run([
                'gcloud', 'compute', 'addresses', 'list', 
                '--global', '--format=json',
                '--filter', f'network="{self.network_name}" AND purpose="VPC_PEERING"'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                for address in json.loads(result.stdout):
                    address_info = {
                        'name': address['name'],
                        'description': address.get('description', ''),
                        'address_type': address.get('addressType', ''),
                        'address': address.get('address', ''),
                        'purpose': address.get('purpose', ''),
                        'prefix_length': address.get('prefixLength'),
                        'network': address.get('network', '').rsplit('/', 1)[-1] if address.get('network') else None
                    }
                    addresses.append(address_info)
                    
        except Exception as e:
            print(f"Error getting global compute addresses: {e}")
            raise ValueError(f"Error getting global compute addresses: {e}")   
        return addresses

    def get_vpc_access_connectors(self) -> List[Dict[str, Any]]:
        """
        Get VPC Access Connectors for the specified network.
        
        Returns:
            List of VPC Access Connector dictionaries
        """
        connectors = []
        
        try:
            # Use gcloud CLI to get global addresses since the API client doesn't have the method
            result = subprocess.run([
                'gcloud', 'compute', 'networks', 'vpc-access', 'connectors', 'list', 
                '--region', self.region, '--format=json',
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
        except Exception as e:
            print(f"Error getting VPC Access Connectors: {e}")
            raise ValueError(f"Error getting VPC Access Connectors: {e}")
        return connectors

    def get_redis_instances(self) -> List[Dict[str, Any]]:
        """
        Get Redis instances for the specified network.
        
        Returns:
            List of Redis instance dictionaries
        """
        instances = []
        
        try:
            # Use gcloud CLI to get Redis instances since the API client requires location
            result = subprocess.run([
                'gcloud', 'redis', 'instances', 'list', 
                '--region', self.region, '--format=json',
                '--filter', f'authorizedNetwork : projects/{self.project_id}/global/networks/{self.network_name}'
            ], capture_output=True, text=True, check=True)

            if result.returncode == 0:
                for instance in json.loads(result.stdout):
                    instance_info = {
                        'name': instance['name'].rsplit('/', 1)[-1],
                        'display_name': instance.get('displayName', ''),
                        'redis_version': instance.get('redisVersion', ''),
                        'tier': instance.get('tier', ''),
                        'memory_size_gb': instance.get('memorySizeGb', 0),
                        'port': instance.get('port', 6379),
                        'authorized_network': instance.get('authorizedNetwork', '').rsplit('/', 1)[-1],
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
                    instances.append(instance_info)
        except Exception as e:
            print(f"Error getting Redis instances: {e}")
            raise ValueError(f"Error getting Redis instances: {e}")
        return instances

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
                '--format=json'
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

    def get_sql_postgres_instances(self) -> List[Dict[str, Any]]:
        """
        Get Cloud SQL PostgreSQL instances for the specified network.
        
        Returns:
            List of PostgreSQL instance dictionaries with databases
        """
        sql_instances = []
        
        try:
            # Use gcloud CLI to get SQL instances
            result = subprocess.run([
                'gcloud', 'sql', 'instances', 'list', 
                '--format=json'
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
                                
                                instance_info = {
                                    'name': instance_name,
                                    'database_version': instance.get('databaseVersion', ''),
                                    'instance_type': instance.get('instanceType', ''),
                                    'machine_type': instance.get('settings', {}).get('tier', ''),
                                    'database_flags': instance.get('settings', {}).get('databaseFlags', []),
                                    'backup_configuration': {
                                        'enabled': instance.get('settings', {}).get('backupConfiguration', {}).get('enabled', False),
                                        'binary_log_enabled': instance.get('settings', {}).get('backupConfiguration', {}).get('binaryLoggingEnabled', False)
                                    } if instance.get('settings', {}).get('backupConfiguration') else None,
                                    'ip_configuration': {
                                        'ipv4_enabled': instance.get('settings', {}).get('ipConfiguration', {}).get('ipv4Enabled', False),
                                        'private_network': instance.get('settings', {}).get('ipConfiguration', {}).get('privateNetwork', '').rsplit('/', 1)[-1]
                                    } if instance.get('settings', {}).get('ipConfiguration') else None,
                                    'availability_type': instance.get('settings', {}).get('availabilityType', ''),
                                    'data_disk_size_gb': instance.get('settings', {}).get('dataDiskSizeGb', 0),
                                    'data_disk_type': instance.get('settings', {}).get('dataDiskType', ''),
                                    'databases': databases
                                }
                                sql_instances.append(instance_info)
        except Exception as e:
            print(f"Error getting PostgreSQL instances: {e}")
            raise ValueError(f"Error getting PostgreSQL instances: {e}")
        return sql_instances

    def get_gcs_buckets(self, name_regex: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get GCS buckets with optional name regex filtering.
        
        Args:
            name_regex: Optional regex pattern to filter buckets by name
            
        Returns:
            List of GCS bucket dictionaries
        """
        buckets = []
        
        try:
            # List all buckets in the project
            bucket_list = self.storage_client.list_buckets()
            
            for bucket in bucket_list:
                # Apply regex filtering if specified
                if name_regex and not re.search(name_regex, bucket.name):
                    continue
                
                # Get bucket details
                bucket_info = {
                    'name': bucket.name,
                    'location': bucket.location,
                    'location_type': bucket.location_type,
                    'storage_class': bucket.storage_class,
                    'versioning_enabled': bucket.versioning_enabled,
                    'uniform_bucket_level_access_enabled': bucket.iam_configuration.uniform_bucket_level_access_enabled if bucket.iam_configuration else False,
                    'public_access_prevention': bucket.iam_configuration.public_access_prevention if bucket.iam_configuration else None,
                    'lifecycle_rules': [
                        {
                            'action': rule.get('action', {}),
                            'condition': rule.get('condition', {})
                        } for rule in list(bucket.lifecycle_rules)
                    ] if bucket.lifecycle_rules else []
                }
                buckets.append(bucket_info)
                
        except Exception as e:
            print(f"Error getting GCS buckets: {e}")
            raise ValueError(f"Error getting GCS buckets: {e}")
        return buckets

    def get_all_resources(self) -> Dict[str, Any]:
        """
        Get all resources from all resource types in one call.
        
        Returns:
            Dictionary containing all resources organized by type
        """
        print(f"Fetching all GCP resources for project: {self.project_id}")
        
        all_resources = {
            'project_id': self.project_id,
            'timestamp': datetime.datetime.now().isoformat(),
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
            'vpc_peer_global_addresses': [],
            'redis_instances': [],
            'sql_postgres_instances': [],
            'gcs_buckets': []
        }
        
        try:
            # Add Compute Network
            print("Added Compute Network: ", self.network_name)
            all_resources['compute_network'] = {
                'name': self.network_name
            }
            
            # Get Compute Subnetworks
            print("Fetching Compute Subnetworks...")
            all_resources['compute_subnetworks'] = self.get_compute_subnetworks()
            print(f"Found {len(all_resources['compute_subnetworks'])} Compute Subnetworks")
            
            # Get NAT Routers
            print("Fetching NAT Routers...")
            all_resources['nat_routers'] = self.get_nat_routers()
            print(f"Found {len(all_resources['nat_routers'])} NAT Routers")
            
            # Get DataProc Clusters
            print("Fetching DataProc Clusters...")
            all_resources['dataproc_cluster'] = self.get_dataproc_clusters()
            print(f"Found {len(all_resources['dataproc_cluster'])} DataProc Cluster")
            
            # Get Cloud Functions
            print("Fetching Cloud Functions...")
            all_resources['cloud_functions'] = self.get_cloudfunctions()
            print(f"Found {len(all_resources['cloud_functions'])} Cloud Functions")

            # Get Cloud Run Services
            print("Fetching Cloud Run Services...")
            all_resources['cloud_run_services'] = self.get_cloudrun()
            print(f"Found {len(all_resources['cloud_run_services'])} Cloud Run Services")
            
            # Get Firewall Rules (filtered by DPC pattern)
            print("Fetching Firewall Rules...")
            all_resources['firewall_rules'] = self.get_firewall_rules('^dpc.*-allow-.*')
            print(f"Found {len(all_resources['firewall_rules'])} Firewall Rules")
            
            # Get Compute Addresses
            print("Fetching Compute Addresses...")
            all_resources['compute_addresses'] = self.get_compute_addresses()
            print(f"Found {len(all_resources['compute_addresses'])} Compute Addresses")
            
            # Get Global Compute Addresses
            print("Fetching Global Compute Addresses...")
            all_resources['vpc_peer_global_addresses'] = self.get_global_compute_addresses()
            print(f"Found {len(all_resources['vpc_peer_global_addresses'])} Global Compute Addresses")
            
            # Get Container Clusters
            print("Fetching Container Clusters...")
            all_resources['container_clusters'] = self.get_container_clusters()
            print(f"Found {len(all_resources['container_clusters'])} Container Clusters")
            
            # Get Redis Instances
            print("Fetching Redis Instances...")
            all_resources['redis_instances'] = self.get_redis_instances()
            print(f"Found {len(all_resources['redis_instances'])} Redis Instances")
            
            # Get PostgreSQL Instances
            print("Fetching PostgreSQL Instances...")
            all_resources['sql_postgres_instances'] = self.get_sql_postgres_instances()
            print(f"Found {len(all_resources['sql_postgres_instances'])} PostgreSQL Instances")
            
            # Get GCS Buckets
            print("Fetching GCS Buckets...")
            if self.mlisa_cluster == 'rai':
                all_resources['gcs_buckets'] = self.get_gcs_buckets('^.*-sa-.*-mlisa-gcs-.*')
            else:
                all_resources['gcs_buckets'] = self.get_gcs_buckets('^.*alto-.*-mlisa-gcs-.*')
            print(f"Found {len(all_resources['gcs_buckets'])} GCS Buckets")
            
            # Get VPC Access Connectors
            #print("Fetching VPC Access Connectors...")
            #all_resources['vpc_access_connectors'] = self.get_vpc_access_connectors()
            #print(f"Found {len(all_resources['vpc_access_connectors'])} VPC Access Connectors")

        except Exception as e:
            print(f"Error fetching all resources: {e}")
            raise ValueError(f"Error fetching all resources: {e}")
        return all_resources


def main():
    """
    Main function to demonstrate usage of GCPResourceReader.
    
    Parses command line arguments and generates resource reports for specified environments.
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
            mlisa_cluster=args.cluster
        )
        print(f"Connected to project: {reader.project_id}")
            
        # Get all resources
        resources = reader.get_all_resources()
        
        # Save results to JSON file
        output_filename = f'./configs/{args.environment}/{args.cluster}.tfvars.json'
        with open(output_filename, 'w') as f:
            json.dump(resources, f, indent=2)
        print(f"Results saved to: {output_filename}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()