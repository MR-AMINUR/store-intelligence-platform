# Configuration Directory

This directory contains configuration files for the Store Intelligence Platform.

## Files

- `zones.json` - Zone definitions for store layout (to be created during setup)

## Zone Configuration Format

The `zones.json` file should follow this structure:

```json
{
  "zones": [
    {
      "zone_id": "zone_001",
      "zone_name": "Cosmetics",
      "zone_type": "GENERAL",
      "polygon": [
        {"x": 100, "y": 100},
        {"x": 300, "y": 100},
        {"x": 300, "y": 300},
        {"x": 100, "y": 300}
      ]
    },
    {
      "zone_id": "billing_queue",
      "zone_name": "Billing Queue",
      "zone_type": "BILLING_QUEUE",
      "polygon": [
        {"x": 500, "y": 400},
        {"x": 700, "y": 400},
        {"x": 700, "y": 600},
        {"x": 500, "y": 600}
      ]
    }
  ]
}
```
