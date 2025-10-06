#!/usr/bin/env python3
"""
Distributed Load Test for vLLM Chat Application
Run this on multiple servers to simulate distributed load
Logs each user's responses to individual files
"""
import argparse
import threading
import time
import requests
import json
from datetime import datetime
import random
import sys
import socket
import os

# Configuration
SERVER_HOST = "192.168.1.1"
SERVER_PORT = "8000"
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
MODEL_ID = "/mnt/data/office_work/vllms_inference/Llama-3.2-3B-Instruct"

TEST_MESSAGES = [
    "What is artificial intelligence?",
    "Explain machine learning in simple terms",
    "How does neural network work?",
    "Tell me about natural language processing",
    "What are the benefits of AI?",
    "Describe deep learning",
    "What is the difference between AI and ML?",
    "How can AI help businesses?",
    "Explain computer vision",
    "What is reinforcement learning?"
]

class DistributedStats:
    def __init__(self, node_id):
        self.node_id = node_id
        self.lock = threading.Lock()
        self.sent = 0
        self.completed = 0
        self.failed = 0
        self.response_times = []
        self.tokens = 0
        self.active = 0
    
    def record_sent(self):
        with self.lock:
            self.sent += 1
    
    def record_completed(self, rt, tok):
        with self.lock:
            self.completed += 1
            self.response_times.append(rt)
            self.tokens += tok
    
    def record_failed(self):
        with self.lock:
            self.failed += 1
    
    def inc_active(self):
        with self.lock:
            self.active += 1
    
    def dec_active(self):
        with self.lock:
            self.active -= 1
    
    def summary(self):
        with self.lock:
            avg_rt = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            return {
                'node': self.node_id,
                'active': self.active,
                'sent': self.sent,
                'completed': self.completed,
                'failed': self.failed,
                'avg_response': avg_rt,
                'total_tokens': self.tokens
            }

def write_user_log(log_dir, node_id, user_id, msg_num, query, response, response_time, token_count, tokens_per_sec, status):
    """Write detailed log for each user message"""
    log_file = os.path.join(log_dir, f"node{node_id}_user{user_id}.txt")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"Message #{msg_num} | {timestamp}\n")
        f.write("=" * 80 + "\n")
        f.write(f"Status:           {status}\n")
        f.write(f"Response Time:    {response_time:.3f}s\n")
        f.write(f"Tokens Generated: {token_count}\n")
        f.write(f"Tokens/Second:    {tokens_per_sec:.2f}\n")
        f.write("-" * 80 + "\n")
        f.write(f"QUERY:\n{query}\n")
        f.write("-" * 80 + "\n")
        f.write(f"RESPONSE:\n{response}\n")
        f.write("=" * 80 + "\n\n")

def write_user_summary(log_dir, node_id, user_id, total_messages, total_time, avg_response, total_tokens):
    """Write summary statistics for each user"""
    log_file = os.path.join(log_dir, f"node{node_id}_user{user_id}.txt")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write("USER SESSION SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Messages:        {total_messages}\n")
        f.write(f"Session Duration:      {total_time:.1f}s\n")
        f.write(f"Avg Response Time:     {avg_response:.2f}s\n")
        f.write(f"Total Tokens:          {total_tokens}\n")
        f.write(f"Avg Tokens/Message:    {total_tokens/total_messages if total_messages > 0 else 0:.1f}\n")
        f.write("=" * 80 + "\n")

def simulate_user(user_id, node_id, duration, stats, log_dir):
    """Simulate user for distributed test with detailed logging"""
    stats.inc_active()
    start = time.time()
    msg_count = 0
    user_response_times = []
    user_total_tokens = 0
    
    # Create initial log file
    log_file = os.path.join(log_dir, f"node{node_id}_user{user_id}.txt")
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Load Test Log - Node {node_id} - User {user_id}\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Target Server: {BASE_URL}\n")
        f.write("=" * 80 + "\n\n")
    
    print(f"[Node {node_id}][User {user_id}] Started")
    
    while time.time() - start < duration:
        try:
            message = random.choice(TEST_MESSAGES)
            payload = {
                "model": MODEL_ID,
                "messages": [{"role": "user", "content": f"[Node{node_id}User{user_id}] {message}"}],
                "temperature": 0.7,
                "max_tokens": 512,
                "stream": True
            }
            
            stats.record_sent()
            req_start = time.time()
            
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                stats.record_failed()
                rt = time.time() - req_start
                write_user_log(log_dir, node_id, user_id, msg_count + 1, message, 
                              f"ERROR: HTTP {response.status_code}", rt, 0, 0, "FAILED")
                print(f"[Node {node_id}][User {user_id}] HTTP Error {response.status_code}")
                time.sleep(random.uniform(3, 8))
                continue
            
            full_resp = ""
            tok_count = 0
            first_token_time = None
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            parsed = json.loads(data)
                            if parsed.get('choices'):
                                content = parsed['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    if first_token_time is None:
                                        first_token_time = time.time()
                                    full_resp += content
                                    tok_count += 1
                        except:
                            continue
            
            rt = time.time() - req_start
            tokens_per_sec = tok_count / rt if rt > 0 else 0
            
            if full_resp:
                stats.record_completed(rt, tok_count)
                msg_count += 1
                user_response_times.append(rt)
                user_total_tokens += tok_count
                
                write_user_log(log_dir, node_id, user_id, msg_count, message, 
                              full_resp, rt, tok_count, tokens_per_sec, "SUCCESS")
                
                print(f"[Node {node_id}][User {user_id}] Msg {msg_count} - {rt:.2f}s - {tok_count} tokens - {tokens_per_sec:.2f} tok/s")
            else:
                stats.record_failed()
                write_user_log(log_dir, node_id, user_id, msg_count + 1, message, 
                              "No response received", rt, 0, 0, "FAILED")
                print(f"[Node {node_id}][User {user_id}] Empty response")
            
            time.sleep(random.uniform(3, 8))
            
        except Exception as e:
            stats.record_failed()
            rt = time.time() - req_start if 'req_start' in locals() else 0
            error_msg = f"Exception: {str(e)}"
            write_user_log(log_dir, node_id, user_id, msg_count + 1, 
                          message if 'message' in locals() else "Unknown", 
                          error_msg, rt, 0, 0, "ERROR")
            print(f"[Node {node_id}][User {user_id}] Error: {e}")
            time.sleep(5)
    
    # Write user summary
    session_time = time.time() - start
    avg_rt = sum(user_response_times) / len(user_response_times) if user_response_times else 0
    write_user_summary(log_dir, node_id, user_id, msg_count, session_time, avg_rt, user_total_tokens)
    
    stats.dec_active()
    print(f"[Node {node_id}][User {user_id}] Finished - {msg_count} messages - Log: {log_file}")

def print_stats_periodic(stats):
    """Print node statistics"""
    while True:
        time.sleep(15)
        s = stats.summary()
        print(f"\n{'='*60}")
        print(f"NODE {s['node']} @ {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Active Users:  {s['active']}")
        print(f"Sent:          {s['sent']}")
        print(f"Completed:     {s['completed']}")
        print(f"Failed:        {s['failed']}")
        print(f"Success Rate:  {(s['completed']/s['sent']*100 if s['sent']>0 else 0):.1f}%")
        print(f"Avg Response:  {s['avg_response']:.2f}s")
        print(f"Total Tokens:  {s['total_tokens']}")
        print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description='Distributed vLLM Load Test with Logging')
    parser.add_argument('--node-id', type=int, required=True, help='Node ID (1-4)')
    parser.add_argument('--users', type=int, default=12, help='Number of concurrent users')
    parser.add_argument('--duration', type=int, default=300, help='Test duration in seconds')
    parser.add_argument('--server', type=str, default='192.168.1.1', help='Server IP')
    parser.add_argument('--port', type=str, default='8000', help='Server port')
    parser.add_argument('--log-dir', type=str, default='load_test_logs', help='Directory for log files')
    
    args = parser.parse_args()
    
    global SERVER_HOST, SERVER_PORT, BASE_URL
    SERVER_HOST = args.server
    SERVER_PORT = args.port
    BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
    
    # Create log directory
    log_dir = args.log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"✓ Created log directory: {log_dir}")
    
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"\n{'='*60}")
    print(f"DISTRIBUTED LOAD TEST - NODE {args.node_id}")
    print(f"{'='*60}")
    print(f"Node ID:       {args.node_id}")
    print(f"Local Host:    {hostname} ({local_ip})")
    print(f"Target Server: {BASE_URL}")
    print(f"Users:         {args.users}")
    print(f"Duration:      {args.duration}s")
    print(f"Log Directory: {os.path.abspath(log_dir)}")
    print(f"{'='*60}\n")
    
    # Test connection
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        if not response.ok:
            print("❌ Server not reachable")
            sys.exit(1)
        print("✓ Server is reachable\n")
    except:
        print("❌ Cannot connect to server")
        sys.exit(1)
    
    stats = DistributedStats(args.node_id)
    
    # Start stats thread
    stats_thread = threading.Thread(target=print_stats_periodic, args=(stats,), daemon=True)
    stats_thread.start()
    
    # Start user threads
    threads = []
    for i in range(args.users):
        user_id = (args.node_id - 1) * args.users + i
        thread = threading.Thread(target=simulate_user, args=(user_id, args.node_id, args.duration, stats, log_dir))
        threads.append(thread)
        thread.start()
        time.sleep(0.2)
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Final results
    s = stats.summary()
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS - NODE {args.node_id}")
    print(f"{'='*60}")
    print(f"Users:         {args.users}")
    print(f"Sent:          {s['sent']}")
    print(f"Completed:     {s['completed']}")
    print(f"Failed:        {s['failed']}")
    print(f"Success Rate:  {(s['completed']/s['sent']*100 if s['sent']>0 else 0):.1f}%")
    print(f"Avg Response:  {s['avg_response']:.2f}s")
    print(f"Total Tokens:  {s['total_tokens']}")
    print(f"{'='*60}")
    print(f"\nLogs saved to: {os.path.abspath(log_dir)}")
    print(f"View user logs: ls {log_dir}/node{args.node_id}_user*.txt")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(0)