output "sql_private_ip_address" {
  description = "The private IP address of the PostgreSQL instances"
  value = tomap({
    for key, sql_ip_output in module.sql_postgres_instances : key => {
      private_ip_address = sql_ip_output.sql_private_ip_address
    }
  })
}

output "dpc_master_node" {
  description = "The name of the DataProc cluster master node"
  value       = [for master in module.dataproc_cluster : master.dpc_master_node]
}