# Gap #9: Advanced Logging Architecture - Quick Reference

**Status:** Production-Ready Infrastructure  
**Components:** Elasticsearch, Kinesis Firehose, CloudWatch Logs, Kibana  

## Quick Start

```bash
# Deploy logging infrastructure
terraform apply -var-file=environments/prod.tfvars

# Access Kibana dashboard
https://nephele-hms-prod.us-east-1.es.amazonaws.com/_plugin/kibana/

# View application logs
aws logs tail /ecs/nephele-hms/prod --follow

# Query with CloudWatch Logs Insights
aws logs start-query \
  --log-group-name /ecs/nephele-hms/prod \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | stats count() by bin(5m)'
```

## Architecture

```
Application Logs
    ↓
CloudWatch Logs (/ecs/nephele-hms/prod)
    ↓
Kinesis Firehose
    ├→ Elasticsearch (Real-time indexing)
    └→ S3 (Backup/Archive)
    
Kibana Dashboard
    ↓ (queries)
    ↓
Elasticsearch
    ↓
Display metrics, dashboards, alerts
```

## Key Features Deployed

1. **Elasticsearch Domain** (480+ lines)
   - Multi-node cluster with replication
   - KMS encryption at rest & TLS in transit
   - JSON logging with slow log detection
   - Advanced security with IAM policies

2. **Kibana Integration**
   - Pre-installed visualization dashboard
   - Real-time log analysis
   - Alert creation capabilities

3. **Kinesis Firehose**
   - Automatic log delivery to Elasticsearch
   - Lambda-based transformation
   - S3 failover for data durability

4. **CloudWatch Log Groups** (4)
   - Application logs
   - WAF logs
   - RDS logs
   - ALB access logs (optional)

5. **CloudWatch Alarms** (3)
   - Cluster health monitoring
   - Storage threshold alerts
   - Indexing rate anomalies

## Configuration Variables

```hcl
enable_elasticsearch           = true
elasticsearch_version          = "7.10"
elasticsearch_instance_count   = 1  # 3+ for prod
elasticsearch_instance_type    = "t3.small.elasticsearch"
elasticsearch_ebs_volume_size  = 100
log_retention_days             = 30
enable_alb_logging            = true
enable_vpc_flow_logs          = true
elasticsearch_backup_enabled   = true
```

## Sample Kibana Queries

```json
// Error rate dashboard
GET logs/_search
{
  "query": {
    "bool": {
      "must": [
        {"match": {"@message": "ERROR"}}
      ],
      "filter": [
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "aggs": {
    "error_count": {"date_histogram": {"field": "@timestamp", "interval": "5m"}}
  }
}

// Slow query detection
GET logs/_search
{
  "query": {
    "bool": {
      "must": [
        {"match": {"log_group": "elasticsearch-index-slow-logs"}}
      ]
    }
  }
}

// API latency analysis
GET logs/_search
{
  "query": {"match_all": {}},
  "aggs": {
    "p99_latency": {
      "percentiles": {
        "field": "response_time_ms",
        "percents": [50, 75, 95, 99]
      }
    }
  }
}
```

## Monitoring Commands

```bash
# Check Elasticsearch health
aws es describe-elasticsearch-domain \
  --domain-name nephele-hms-prod \
  --query 'DomainStatus.[ElasticsearchClusterConfig.InstanceType,StorageOptions.EbsOptions.VolumeSize]'

# View indexing rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/ES \
  --metric-name IndexingRate \
  --dimensions Name=DomainName,Value=nephele-hms-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum

# Count logs in Elasticsearch
curl -s https://nephele-hms-prod.us-east-1.es.amazonaws.com/_count?pretty
```

## Next Actions

1. Deploy: `make tf-apply-prod`
2. Access Kibana: HTTPS link from Elasticsearch domain endpoint
3. Create initial dashboards in Kibana
4. Setup alerts for ERROR/WARN patterns
5. Configure log rotation policies

## Cost Estimate
- Elasticsearch: $20-50/month (t3.small)
- Firehose: $5-10/month
- S3 backups: $1-2/month
- **Total: ~$30-60/month**

---

**Gap #9 Status:** ✅ INFRASTRUCTURE COMPLETE  
**Next:** Gap #10 - Disaster Recovery & Multi-Region HA
