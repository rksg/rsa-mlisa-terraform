output "dpc_master_node" {
  description = "The name of the DataProc cluster master node"
  value       = "${google_dataproc_cluster.dpc_cluster.cluster_config[0].master_config[0].instance_names[0]}.${google_dataproc_cluster.dpc_cluster.cluster_config[0].gce_cluster_config[0].zone}.c.${var.project}.internal"
}
