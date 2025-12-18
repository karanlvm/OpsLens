"""Generate realistic synthetic data for testing and demos."""
from app.db import SessionLocal
from app.db.models import Incident, TimelineEvent, EvidenceItem, Runbook, Hypothesis, Action
from datetime import datetime, timedelta
import random
import uuid


# Realistic incident scenarios
INCIDENT_SCENARIOS = [
    {
        "title": "Database connection pool exhaustion",
        "description": "User service unable to connect to PostgreSQL. Connection pool maxed out at 100 connections. Users experiencing 503 errors.",
        "severity": "critical",
        "status": "investigating",
        "timeline": [
            {"minutes": 0, "type": "alert", "source": "pagerduty", "title": "High connection count alert", "description": "PostgreSQL connection count at 98/100"},
            {"minutes": 5, "type": "alert", "source": "pagerduty", "title": "503 errors spiking", "description": "Error rate increased to 15% on user-service"},
            {"minutes": 10, "type": "log_error", "source": "grafana", "title": "Connection pool exhausted", "description": "java.sql.SQLException: Connection pool exhausted"},
            {"minutes": 15, "type": "deployment", "source": "github", "title": "PR #1243 merged", "description": "Increased connection pool size from 50 to 100"},
            {"minutes": 20, "type": "metric_spike", "source": "datadog", "title": "Connection count normalized", "description": "Connections dropped to 45/100 after pool increase"},
        ],
        "evidence": [
            {"type": "log", "title": "Application logs - connection errors", "content": "2025-12-18 10:15:23 ERROR [pool-1] Unable to acquire connection: pool exhausted\n2025-12-18 10:15:24 ERROR [pool-1] Unable to acquire connection: pool exhausted\n2025-12-18 10:15:25 ERROR [pool-1] Unable to acquire connection: pool exhausted"},
            {"type": "metric", "title": "PostgreSQL connection metrics", "content": "Connection count: 98/100\nActive queries: 95\nIdle connections: 3\nWait time: 2.3s average"},
            {"type": "pr", "title": "GitHub PR #1243", "content": "Increase database connection pool size\n- Changed max connections from 50 to 100\n- Updated connection timeout to 30s\n- Added connection pool monitoring"},
        ],
        "hypotheses": [
            {"title": "Connection pool too small for traffic spike", "description": "The connection pool size of 50 was insufficient for the current traffic load. Recent traffic increase (likely from marketing campaign) caused all connections to be exhausted.", "confidence": 0.85, "status": "confirmed"},
        ],
        "actions": [
            {"title": "Increase connection pool size", "description": "Deploy PR #1243 to increase pool from 50 to 100", "type": "deployment", "status": "completed"},
            {"title": "Monitor connection usage", "description": "Set up alerts for connection pool > 80%", "type": "monitoring", "status": "pending"},
            {"title": "Review connection leak", "description": "Check for potential connection leaks in user-service code", "type": "investigation", "status": "pending"},
        ]
    },
    {
        "title": "Payment service memory leak after deployment",
        "description": "Payment service memory usage growing continuously after deployment v2.4.1. Service restarts required every 4 hours. Affecting 5% of payment transactions.",
        "severity": "high",
        "status": "investigating",
        "timeline": [
            {"minutes": 0, "type": "alert", "source": "pagerduty", "title": "Memory usage > 90%", "description": "payment-service pod memory at 2.8GB/3GB"},
            {"minutes": 30, "type": "deployment", "source": "github", "title": "Deployment v2.4.1", "description": "Merged PR #1189: Add caching layer for payment methods"},
            {"minutes": 60, "type": "metric_spike", "source": "datadog", "title": "Memory growth detected", "description": "Memory increasing at 50MB/hour"},
            {"minutes": 90, "type": "manual_action", "source": "manual", "title": "Service restarted", "description": "Manual restart to clear memory"},
            {"minutes": 120, "type": "log_error", "source": "grafana", "title": "OutOfMemoryError", "description": "java.lang.OutOfMemoryError: Java heap space"},
        ],
        "evidence": [
            {"type": "log", "title": "Heap dump analysis", "content": "Heap analysis shows 1.2GB of cached payment method objects\nCache never expires\nObjects accumulating in memory"},
            {"type": "metric", "title": "Memory usage graph", "content": "Memory: 1.2GB → 1.8GB → 2.4GB → 2.8GB over 4 hours\nGC frequency: Increasing\nHeap usage: 95%"},
            {"type": "pr", "title": "GitHub PR #1189", "content": "Added in-memory cache for payment methods\n- Cache size: unlimited\n- TTL: None (intended to be permanent)\n- Issue: No eviction policy"},
        ],
        "hypotheses": [
            {"title": "Cache without eviction policy", "description": "The new caching layer in v2.4.1 has no eviction policy. Payment method objects are cached indefinitely and never removed, causing memory to grow continuously.", "confidence": 0.92, "status": "confirmed"},
        ],
        "actions": [
            {"title": "Add cache TTL", "description": "Implement 24-hour TTL for payment method cache", "type": "fix", "status": "in_progress"},
            {"title": "Rollback deployment", "description": "Consider rolling back v2.4.1 if memory leak continues", "type": "rollback", "status": "pending"},
            {"title": "Add memory alerts", "description": "Set up alerts for memory > 80%", "type": "monitoring", "status": "pending"},
        ]
    },
    {
        "title": "API gateway rate limiting misconfiguration",
        "description": "Legitimate API traffic being rate limited incorrectly. Customer API calls failing with 429 errors. Affecting 20% of API requests.",
        "severity": "high",
        "status": "resolved",
        "timeline": [
            {"minutes": 0, "type": "alert", "source": "pagerduty", "title": "High 429 error rate", "description": "429 rate limit errors at 20% of requests"},
            {"minutes": 10, "type": "log_error", "source": "grafana", "title": "Rate limit logs", "description": "Multiple IPs hitting rate limit: 100 req/min"},
            {"minutes": 20, "type": "deployment", "source": "github", "title": "Config change deployed", "description": "Updated rate limit config: 50 req/min → 200 req/min"},
            {"minutes": 25, "type": "metric_spike", "source": "datadog", "title": "429 errors dropped", "description": "Error rate normalized to < 1%"},
        ],
        "evidence": [
            {"type": "log", "title": "Rate limit logs", "content": "2025-12-18 09:30:15 WARN [gateway] Rate limit exceeded for IP 192.168.1.100: 101 requests in 60s\n2025-12-18 09:30:16 WARN [gateway] Rate limit exceeded for IP 192.168.1.101: 102 requests in 60s"},
            {"type": "metric", "title": "API error rate", "content": "429 errors: 20% of requests\nTotal requests: 10,000/min\nRate limited: 2,000/min"},
        ],
        "hypotheses": [
            {"title": "Rate limit too aggressive", "description": "Rate limit of 50 req/min was too low for legitimate customer traffic. Many customers have automated systems that make > 50 requests per minute.", "confidence": 0.88, "status": "confirmed"},
        ],
        "actions": [
            {"title": "Increase rate limit", "description": "Update rate limit from 50 to 200 req/min", "type": "config", "status": "completed"},
            {"title": "Review rate limit logic", "description": "Consider per-customer rate limits instead of per-IP", "type": "investigation", "status": "pending"},
        ]
    },
    {
        "title": "Redis cache cluster failure",
        "description": "Primary Redis node failed, causing cache misses and increased database load. Session data lost. Users logged out.",
        "severity": "critical",
        "status": "resolved",
        "timeline": [
            {"minutes": 0, "type": "alert", "source": "pagerduty", "title": "Redis node down", "description": "redis-primary-1: Connection refused"},
            {"minutes": 2, "type": "alert", "source": "pagerduty", "title": "High database load", "description": "PostgreSQL CPU at 85%, query time increased 5x"},
            {"minutes": 5, "type": "log_error", "source": "grafana", "title": "Cache connection errors", "description": "redis.exceptions.ConnectionError: Error connecting to redis-primary-1"},
            {"minutes": 10, "type": "manual_action", "source": "manual", "title": "Failover to replica", "description": "Promoted redis-replica-1 to primary"},
            {"minutes": 15, "type": "metric_spike", "source": "datadog", "title": "Cache restored", "description": "Redis connections restored, cache hit rate back to 95%"},
        ],
        "evidence": [
            {"type": "log", "title": "Redis connection logs", "content": "2025-12-18 08:15:00 ERROR [cache] Failed to connect to redis-primary-1:6379\n2025-12-18 08:15:01 ERROR [cache] Connection timeout after 5s"},
            {"type": "metric", "title": "Cache hit rate", "content": "Before: 95% hit rate\nDuring: 0% hit rate (all misses)\nAfter: 95% hit rate"},
            {"type": "trace", "title": "Database query latency", "content": "Average query time: 50ms → 250ms\nCache miss rate: 5% → 100%"},
        ],
        "hypotheses": [
            {"title": "Redis node hardware failure", "description": "Primary Redis node experienced hardware failure. Automatic failover should have triggered but didn't. Manual intervention required to promote replica.", "confidence": 0.75, "status": "confirmed"},
        ],
        "actions": [
            {"title": "Failover to replica", "description": "Promote redis-replica-1 to primary", "type": "manual", "status": "completed"},
            {"title": "Investigate failover automation", "description": "Why didn't automatic failover trigger?", "type": "investigation", "status": "pending"},
            {"title": "Add Redis health checks", "description": "Improve monitoring and alerting for Redis cluster", "type": "monitoring", "status": "pending"},
        ]
    },
    {
        "title": "Authentication service JWT token validation failure",
        "description": "Users unable to authenticate. JWT tokens being rejected as invalid. Affecting all new login attempts.",
        "severity": "critical",
        "status": "resolved",
        "timeline": [
            {"minutes": 0, "type": "alert", "source": "pagerduty", "title": "Auth service errors", "description": "Error rate at 100% for token validation"},
            {"minutes": 5, "type": "log_error", "source": "grafana", "title": "JWT validation errors", "description": "jwt.exceptions.InvalidTokenError: Token signature invalid"},
            {"minutes": 10, "type": "deployment", "source": "github", "title": "Config update deployed", "description": "Updated JWT secret key in auth-service config"},
            {"minutes": 12, "type": "metric_spike", "source": "datadog", "title": "Auth errors resolved", "description": "Error rate dropped to 0%, login success rate back to normal"},
        ],
        "evidence": [
            {"type": "log", "title": "JWT validation logs", "content": "2025-12-18 07:45:00 ERROR [auth] JWT signature verification failed\n2025-12-18 07:45:01 ERROR [auth] Invalid token: signature mismatch"},
            {"type": "metric", "title": "Authentication success rate", "content": "Before: 99.5% success\nDuring: 0% success (all failures)\nAfter: 99.5% success"},
            {"type": "pr", "title": "GitHub PR #1156", "content": "Updated JWT secret key rotation\n- New secret deployed\n- Old tokens invalidated\n- Users need to re-login"},
        ],
        "hypotheses": [
            {"title": "JWT secret key mismatch", "description": "JWT secret key was rotated but the new key wasn't properly deployed to auth-service. Service was still using old key to validate tokens signed with new key.", "confidence": 0.95, "status": "confirmed"},
        ],
        "actions": [
            {"title": "Deploy new JWT secret", "description": "Update auth-service config with new JWT secret key", "type": "config", "status": "completed"},
            {"title": "Review secret rotation process", "description": "Improve secret rotation to prevent mismatches", "type": "investigation", "status": "pending"},
        ]
    },
]


def generate_synthetic_incidents():
    """Generate realistic incidents with coherent timelines and evidence."""
    db = SessionLocal()
    try:
        for scenario in INCIDENT_SCENARIOS:
            # Create incident
            incident = Incident(
                title=scenario["title"],
                description=scenario["description"],
                severity=scenario["severity"],
                status=scenario["status"],
                created_at=datetime.utcnow() - timedelta(hours=random.randint(2, 24))
            )
            db.add(incident)
            db.flush()
            
            # Create timeline events
            for event_data in scenario["timeline"]:
                event = TimelineEvent(
                    incident_id=incident.id,
                    timestamp=incident.created_at + timedelta(minutes=event_data["minutes"]),
                    event_type=event_data["type"],
                    title=event_data["title"],
                    description=event_data["description"],
                    source=event_data["source"],
                    source_id=str(uuid.uuid4()),
                    event_metadata={}
                )
                db.add(event)
            
            # Create evidence items
            for evidence_data in scenario["evidence"]:
                evidence = EvidenceItem(
                    incident_id=incident.id,
                    evidence_type=evidence_data["type"],
                    title=evidence_data["title"],
                    content=evidence_data["content"],
                    source=evidence_data.get("source", "system"),
                    created_at=incident.created_at + timedelta(minutes=random.randint(0, 30))
                )
                db.add(evidence)
            
            # Create hypotheses
            for hyp_data in scenario["hypotheses"]:
                evidence_ids = [str(e.id) for e in db.query(EvidenceItem).filter(
                    EvidenceItem.incident_id == incident.id
                ).limit(2).all()]
                
                hypothesis = Hypothesis(
                    incident_id=incident.id,
                    title=hyp_data["title"],
                    description=hyp_data["description"],
                    confidence=hyp_data["confidence"],
                    rank=1,
                    status=hyp_data["status"],
                    supporting_evidence=evidence_ids
                )
                db.add(hypothesis)
            
            # Create actions
            for action_data in scenario["actions"]:
                action = Action(
                    incident_id=incident.id,
                    title=action_data["title"],
                    description=action_data["description"],
                    action_type=action_data["type"],
                    status=action_data["status"],
                    created_at=incident.created_at + timedelta(minutes=random.randint(5, 60))
                )
                if action_data["status"] == "completed":
                    action.completed_at = incident.created_at + timedelta(minutes=random.randint(15, 90))
                db.add(action)
        
        db.commit()
        print(f"Generated {len(INCIDENT_SCENARIOS)} realistic incidents with coherent timelines, evidence, hypotheses, and actions.")
        
    finally:
        db.close()


def generate_synthetic_runbooks():
    """Generate realistic runbooks."""
    db = SessionLocal()
    try:
        runbooks_data = [
            {
                "title": "Database Connection Pool Exhaustion",
                "description": "Troubleshoot and resolve database connection pool exhaustion issues",
                "service": "database",
                "content": """# Database Connection Pool Exhaustion

## Symptoms
- High number of active database connections
- Connection timeout errors in application logs
- 503 Service Unavailable errors
- Slow query response times

## Diagnosis Steps
1. Check current connection count:
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

2. Review connection pool metrics in Grafana
3. Check for connection leaks in application logs
4. Verify connection pool configuration

## Resolution
1. Increase connection pool size (if traffic increased)
2. Fix connection leaks in code
3. Add connection timeout and retry logic
4. Consider connection pooling at application level

## Prevention
- Monitor connection pool usage (alert at 80%)
- Set up connection leak detection
- Regular code reviews for connection handling
- Load testing before deployments
""",
                "tags": ["database", "critical", "connection-pool"]
            },
            {
                "title": "Memory Leak Investigation",
                "description": "Identify and fix memory leaks in Java services",
                "service": "api",
                "content": """# Memory Leak Investigation

## Symptoms
- Continuous memory growth over time
- Frequent garbage collection
- OutOfMemoryError exceptions
- Service requires frequent restarts

## Diagnosis Steps
1. Generate heap dump:
   ```bash
   jmap -dump:format=b,file=heap.bin <pid>
   ```

2. Analyze heap dump with Eclipse MAT or jhat
3. Check for objects that shouldn't be accumulating
4. Review recent code changes (especially caching)

## Resolution
1. Fix the root cause (unbounded cache, listener leaks, etc.)
2. Add proper eviction policies
3. Set memory limits and alerts
4. Consider rolling back problematic deployment

## Prevention
- Code reviews for caching implementations
- Memory profiling in CI/CD
- Set memory alerts at 80%
- Regular heap dump analysis
""",
                "tags": ["memory", "java", "performance"]
            },
            {
                "title": "Redis Failover Procedure",
                "description": "Handle Redis primary node failure and failover to replica",
                "service": "cache",
                "content": """# Redis Failover Procedure

## Symptoms
- Redis connection errors
- Cache miss rate spike
- Increased database load
- Application errors

## Diagnosis Steps
1. Check Redis node status:
   ```bash
   redis-cli -h redis-primary ping
   ```

2. Verify replica nodes are healthy
3. Check Redis sentinel status (if using sentinel)
4. Review application connection logs

## Resolution
1. If using sentinel: Wait for automatic failover (usually 30s)
2. Manual failover: Promote replica to primary
   ```bash
   redis-cli -h redis-replica REPLICAOF NO ONE
   ```
3. Update application config to point to new primary
4. Restart affected services

## Prevention
- Use Redis Sentinel for automatic failover
- Regular health checks and monitoring
- Test failover procedures regularly
- Document failover runbook
""",
                "tags": ["redis", "cache", "failover", "critical"]
            },
            {
                "title": "Rate Limit Misconfiguration",
                "description": "Fix incorrect API rate limiting causing legitimate traffic to be blocked",
                "service": "api",
                "content": """# Rate Limit Misconfiguration

## Symptoms
- High 429 (Too Many Requests) error rate
- Legitimate users unable to access API
- Customer complaints about API access
- Sudden increase in error rate

## Diagnosis Steps
1. Check rate limit configuration in API gateway
2. Review rate limit logs for patterns
3. Identify if rate limits are per-IP, per-user, or global
4. Compare current traffic vs. historical baseline

## Resolution
1. Adjust rate limit thresholds appropriately
2. Consider per-customer limits instead of per-IP
3. Whitelist known good IPs if needed
4. Deploy updated configuration
5. Monitor error rate after change

## Prevention
- Load test rate limits before deployment
- Monitor 429 error rates
- Use gradual rollout for rate limit changes
- Document rate limit policies clearly
""",
                "tags": ["api", "rate-limiting", "configuration"]
            },
            {
                "title": "JWT Token Validation Issues",
                "description": "Troubleshoot JWT token validation failures in authentication service",
                "service": "auth",
                "content": """# JWT Token Validation Issues

## Symptoms
- All authentication requests failing
- Invalid token errors in logs
- Users unable to login
- JWT signature verification errors

## Diagnosis Steps
1. Check JWT secret key configuration
2. Verify secret key matches between services
3. Check token expiration settings
4. Review recent secret key rotations

## Resolution
1. Ensure JWT secret is correctly configured
2. If secret was rotated, update all services
3. Verify token signing and validation use same secret
4. Test authentication after fix
5. May need to invalidate existing tokens

## Prevention
- Coordinate secret rotations across all services
- Use secret management system (Vault, AWS Secrets Manager)
- Test authentication after secret changes
- Monitor authentication success rate
""",
                "tags": ["auth", "jwt", "security", "critical"]
            },
        ]
        
        for runbook_data in runbooks_data:
            runbook = Runbook(
                title=runbook_data["title"],
                description=runbook_data["description"],
                content=runbook_data["content"],
                service=runbook_data["service"],
                tags=runbook_data["tags"]
            )
            db.add(runbook)
        
        db.commit()
        print(f"Generated {len(runbooks_data)} realistic runbooks.")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("Generating realistic synthetic data...")
    generate_synthetic_incidents()
    generate_synthetic_runbooks()
    print("Done!")
