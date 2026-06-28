"""Event Sender for CV Pipeline.

This module sends generated events to the Store Intelligence Platform
backend API via HTTP POST requests with batching and retry logic.
"""

import logging
import time
from typing import List

import requests

from pipeline.event_generator import Event

# Configure logging
logger = logging.getLogger(__name__)


class EventSender:
    """Sends events to backend API.
    
    Batches events and sends them to the /events/ingest endpoint
    with automatic retry on failure.
    
    Attributes:
        base_url: Backend API base URL
        ingest_endpoint: Event ingestion endpoint path
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries
        batch_size: Number of events per batch
    """
    
    def __init__(
        self,
        base_url: str,
        ingest_endpoint: str = "/events/ingest",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        batch_size: int = 50,
    ):
        """Initialize event sender.
        
        Args:
            base_url: Backend API base URL (e.g., http://localhost:8000)
            ingest_endpoint: Ingestion endpoint path
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            batch_size: Events per batch
        """
        self.base_url = base_url.rstrip('/')
        self.ingest_endpoint = ingest_endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        
        self.events_sent = 0
        self.events_failed = 0
        self.batches_sent = 0
        
        logger.info(f"EventSender initialized (base_url={base_url}, batch_size={batch_size})")
    
    def send_events(self, events: List[Event]) -> bool:
        """Send events to backend API.
        
        Args:
            events: List of events to send
            
        Returns:
            True if all events sent successfully, False otherwise
        """
        if not events:
            return True
        
        # Send in batches
        total_events = len(events)
        success = True
        
        for i in range(0, total_events, self.batch_size):
            batch = events[i:i + self.batch_size]
            batch_success = self._send_batch(batch)
            
            if not batch_success:
                success = False
                logger.error(f"Batch {i//self.batch_size + 1} failed")
        
        return success
    
    def _send_batch(self, events: List[Event]) -> bool:
        """Send a batch of events with retry logic.
        
        Args:
            events: Batch of events
            
        Returns:
            True if batch sent successfully
        """
        url = f"{self.base_url}{self.ingest_endpoint}"
        
        # Convert events to API format
        payload = [event.to_dict() for event in events]
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Sending batch of {len(events)} events (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code == 201:
                    result = response.json()
                    events_processed = result.get("events_processed", 0)
                    
                    self.events_sent += events_processed
                    self.batches_sent += 1
                    
                    logger.info(f"Batch sent successfully: {events_processed} events processed")
                    return True
                    
                else:
                    logger.warning(
                        f"Batch send failed with status {response.status_code}: {response.text}"
                    )
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error sending batch: {e}")
            
            # Retry delay
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        # All retries failed
        self.events_failed += len(events)
        logger.error(f"Batch send failed after {self.max_retries} attempts")
        return False
    
    def health_check(self) -> bool:
        """Check if backend API is reachable.
        
        Returns:
            True if API is healthy
        """
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info("Backend API health check passed")
                return True
            else:
                logger.warning(f"Backend API health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Backend API health check failed: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get sender statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "events_sent": self.events_sent,
            "events_failed": self.events_failed,
            "batches_sent": self.batches_sent,
            "success_rate": self.events_sent / (self.events_sent + self.events_failed)
            if (self.events_sent + self.events_failed) > 0
            else 0.0,
        }
