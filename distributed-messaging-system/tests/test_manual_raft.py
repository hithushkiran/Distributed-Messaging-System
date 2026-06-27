"""
Manual Raft Consensus - Test Script
Author: ABEYRATHNA J G D A (IT23424432)

This script tests the manual Raft implementation:
- Leader election
- Heartbeat mechanism
- Failover when leader crashes

Run this to verify the consensus algorithm works correctly.
"""

import sys
import os
import time
import threading

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from consensus.raft_node import RaftNode


def test_leader_election():
    """Test basic leader election with 3 nodes"""
    print("=" * 60)
    print("TEST: Leader Election with 3 Nodes")
    print("=" * 60)
    
    # Define cluster
    cluster_nodes = [
        '127.0.0.1:5000',
        '127.0.0.1:5001',
        '127.0.0.1:5002'
    ]
    
    # Create three Raft nodes
    print("\n[1] Creating 3 Raft nodes...")
    node1 = RaftNode('127.0.0.1:5000', cluster_nodes)
    node2 = RaftNode('127.0.0.1:5001', cluster_nodes)
    node3 = RaftNode('127.0.0.1:5002', cluster_nodes)
    
    # Start all nodes
    print("\n[2] Starting all nodes...")
    node1.start()
    time.sleep(0.1)
    node2.start()
    time.sleep(0.1)
    node3.start()
    
    # Wait for election
    print("\n[3] Waiting for leader election (5 seconds)...")
    time.sleep(5)
    
    # Check results
    print("\n[4] Election Results:")
    print("-" * 60)
    
    state1 = node1.get_state()
    state2 = node2.get_state()
    state3 = node3.get_state()
    
    print(f"Node 1: {state1['state']:>10} | Term: {state1['term']} | Leader: {state1['leader']}")
    print(f"Node 2: {state2['state']:>10} | Term: {state2['term']} | Leader: {state2['leader']}")
    print(f"Node 3: {state3['state']:>10} | Term: {state3['term']} | Leader: {state3['leader']}")
    
    # Verify exactly one leader
    leaders = []
    for node, state in [(node1, state1), (node2, state2), (node3, state3)]:
        if node.is_leader():
            leaders.append(state['node_id'])
    
    print("\n[5] Verification:")
    print(f"  - Number of leaders: {len(leaders)}")
    print(f"  - Leader(s): {leaders}")
    
    if len(leaders) == 1:
        print("  ✓ SUCCESS: Exactly one leader elected")
    else:
        print("  ✗ FAIL: Should have exactly one leader")
    
    # Check if all nodes agree on leader
    leader_consensus = state1['leader'] == state2['leader'] == state3['leader']
    if leader_consensus:
        print(f"  ✓ SUCCESS: All nodes agree on leader: {state1['leader']}")
    else:
        print("  ✗ FAIL: Nodes don't agree on leader")
    
    # Test heartbeat
    print("\n[6] Testing heartbeat mechanism (10 seconds)...")
    for i in range(10):
        time.sleep(1)
        leader_count = sum([1 for n in [node1, node2, node3] if n.is_leader()])
        print(f"  After {i+1}s: {leader_count} leader(s)")
        if leader_count != 1:
            print("  ✗ WARNING: Leader count changed!")
    
    # Stop all nodes
    print("\n[7] Stopping all nodes...")
    node1.stop()
    node2.stop()
    node3.stop()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


def test_leader_failover():
    """Test leader failover when current leader crashes"""
    print("\n\n")
    print("=" * 60)
    print("TEST: Leader Failover")
    print("=" * 60)
    
    # Define cluster
    cluster_nodes = [
        '127.0.0.1:5000',
        '127.0.0.1:5001',
        '127.0.0.1:5002'
    ]
    
    # Create and start nodes
    print("\n[1] Creating and starting 3 nodes...")
    node1 = RaftNode('127.0.0.1:5000', cluster_nodes)
    node2 = RaftNode('127.0.0.1:5001', cluster_nodes)
    node3 = RaftNode('127.0.0.1:5002', cluster_nodes)
    
    node1.start()
    time.sleep(0.1)
    node2.start()
    time.sleep(0.1)
    node3.start()
    
    # Wait for initial election
    print("\n[2] Waiting for initial leader election...")
    time.sleep(5)
    
    # Find current leader
    nodes = [node1, node2, node3]
    leader_node = None
    for node in nodes:
        if node.is_leader():
            leader_node = node
            break
    
    if not leader_node:
        print("  ✗ FAIL: No leader found")
        return
    
    print(f"\n[3] Current leader: {leader_node.node_id}")
    
    # Stop the leader
    print(f"\n[4] Stopping leader {leader_node.node_id}...")
    leader_node.stop()
    
    # Wait for new election
    print("\n[5] Waiting for new leader election (5 seconds)...")
    time.sleep(5)
    
    # Check if new leader elected
    print("\n[6] Checking for new leader:")
    new_leader_count = 0
    for node in nodes:
        if node.running and node.is_leader():
            new_leader_count += 1
            print(f"  ✓ New leader: {node.node_id}")
    
    if new_leader_count == 1:
        print("  ✓ SUCCESS: New leader elected after failover")
    else:
        print(f"  ✗ FAIL: Expected 1 new leader, found {new_leader_count}")
    
    # Stop remaining nodes
    print("\n[7] Stopping remaining nodes...")
    for node in nodes:
        if node.running:
            node.stop()
    
    print("\n" + "=" * 60)
    print("FAILOVER TEST COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    print("\n")
    print("*" * 60)
    print("  MANUAL RAFT CONSENSUS - TEST SUITE")
    print("  Author: ABEYRATHNA J G D A (IT23424432)")
    print("*" * 60)
    
    try:
        # Test 1: Basic leader election
        test_leader_election()
        
        # Test 2: Leader failover
        test_leader_failover()
        
        print("\n\n" + "*" * 60)
        print("  ALL TESTS COMPLETE")
        print("*" * 60)
    
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
