output "cluster_name" {
  description = "The name of the created DataProc cluster"
  value       = google_dataproc_cluster.dpc_cluster.name
}
