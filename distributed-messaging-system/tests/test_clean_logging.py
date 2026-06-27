"""
Test Clean Logging - Compare Demo vs Verbose modes

Run this to see the difference between clean and verbose logging
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from logging_config import setup_demo_logging, setup_standard_logging
import logging

def test_logging_modes():
    print("\n" + "="*70)
    print("DEMO MODE TEST (Clean Output)")
    print("="*70)
    
    setup_demo_logging(verbose=False)
    
    logger = logging.getLogger("TestLogger")
    
    # These should show (important events)
    logger.info("✓ Elected as LEADER for term 1")
    logger.info("Node 0 FAILED - starting election")
    logger.info("Message replicated to all followers")
    logger.warning("Health check failed for node 2")
    logger.info("Cluster formed with 3 nodes")
    
    # These should NOT show (noise)
    logger.info("Connection from 127.0.0.1:50231")
    logger.info("Connection closed")
    logger.info("Sending heartbeat to node 1")
    logger.info("Received heartbeat from leader")
    logger.info("Health check to 127.0.0.1:5001")
    logger.info("TCP connection established")
    
    print("\n" + "="*70)
    print("📝 Note: Filtered messages are still saved to full_system.log")
    print("="*70)
    
    input("\n\nPress Enter to see VERBOSE MODE (all logs)...")
    
    print("\n" + "="*70)
    print("VERBOSE MODE TEST (All Output)")
    print("="*70)
    
    # Remove all handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    
    setup_demo_logging(verbose=True)
    
    logger2 = logging.getLogger("TestLogger2")
    
    # Now ALL should show
    logger2.info("✓ Elected as LEADER for term 1")
    logger2.info("Node 0 FAILED - starting election")
    logger2.info("Message replicated to all followers")
    logger2.warning("Health check failed for node 2")
    logger2.info("Cluster formed with 3 nodes")
    logger2.info("Connection from 127.0.0.1:50231")
    logger2.info("Connection closed")
    logger2.info("Sending heartbeat to node 1")
    logger2.info("Received heartbeat from leader")
    logger2.info("Health check to 127.0.0.1:5001")
    logger2.info("TCP connection established")
    
    print("\n" + "="*70)
    print("✅ Test Complete!")
    print("="*70)
    print("\nFor your demo, use:")
    print("  setup_demo_logging(verbose=False)  # Clean output")
    print("\nFor debugging, use:")
    print("  setup_demo_logging(verbose=True)   # All output")
    print("="*70)

if __name__ == "__main__":
    test_logging_modes()
