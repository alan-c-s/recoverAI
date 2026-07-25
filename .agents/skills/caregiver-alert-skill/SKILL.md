---
name: caregiver-alert-skill
description: Risk assessment classification, emergency escalation rules, and automated caregiver notification protocols for RecoverAI.
---

# Caregiver Alert & Escalation Skill

## Overview
Guides the classification of patient risk tiers and governs automated notification dispatch to designated caregivers and clinical teams.

## Risk Tier Matrix

| Risk Tier | Criteria / Indicators | Automated Action |
| :--- | :--- | :--- |
| **Tier 1 (Low)** | Normal mood (6-10), no cravings, positive reflection. | Log session. No notification. |
| **Tier 2 (Medium)** | Mild craving (1-4), elevated stress, fatigue. | Suggest coping exercise. Log in timeline. |
| **Tier 3 (High)** | High craving (5-8), isolated feeling, negative sentiment drop. | Dispatch Push / Email alert to caregiver. |
| **Tier 4 (Critical)** | Severe craving (9-10), self-harm intent, crisis keywords. | Trigger SMS + Push + Call to caregiver. Display 988 lifeline. |

## Dispatch Protocols

1. **Redis Pub/Sub Event**: Publish event to `patient:{patient_id}:alerts` channel.
2. **WebSocket Broadcast**: Piped to Caregiver Dashboard connected socket.
3. **SMS Dispatch**: Trigger Twilio emergency notification to primary caregiver phone.
4. **Audit Trail**: Record alert ID, timestamp, and acknowledgment status in `risk_alerts` table.
