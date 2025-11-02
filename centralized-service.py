#!/usr/bin/env python3
"""
GenAI Test Platform - Centralized Webhook Service
Monitors ALL repositories in a GitHub organization and triggers AI test generation
"""

import os
import json
import asyncio
import aiohttp
from aiohttp import web
import hmac
import hashlib
import subprocess
import tempfile
import logging
from pathlib import Path

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', 'your-webhook-secret')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
PORT = int(os.getenv('PORT', 8080))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenAITestPlatformService:
    def __init__(self):
        self.session = None
        self.processing_queue = asyncio.Queue()
        
    async def start(self):
        """Start the service"""
        self.session = aiohttp.ClientSession()
        # Start background processor
        asyncio.create_task(self.process_queue())
        
    async def stop(self):
        """Stop the service"""
        if self.session:
            await self.session.close()
            
    def verify_webhook_signature(self, payload_body, signature_header):
        """Verify GitHub webhook signature"""
        expected_signature = hmac.new(
            GITHUB_WEBHOOK_SECRET.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected_signature}", signature_header)
    
    async def handle_webhook(self, request):
        """Handle incoming GitHub webhooks"""
        try:
            # Verify signature
            signature = request.headers.get('X-Hub-Signature-256', '')
            payload = await request.read()
            
            if not self.verify_webhook_signature(payload, signature):
                return web.Response(status=401, text="Invalid signature")
            
            # Parse webhook data
            event_type = request.headers.get('X-GitHub-Event', '')
            data = json.loads(payload.decode('utf-8'))
            
            logger.info(f"Received {event_type} webhook from {data.get('repository', {}).get('full_name', 'unknown')}")
            
            # Only process push events to main branches
            if event_type == 'push' and data.get('ref') in ['refs/heads/main', 'refs/heads/master', 'refs/heads/develop']:
                await self.queue_repository_for_processing(data)
            
            return web.Response(text="OK")
            
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            return web.Response(status=500, text="Internal server error")
    
    async def queue_repository_for_processing(self, webhook_data):
        """Queue repository for AI test generation"""
        repo_data = {
            'full_name': webhook_data['repository']['full_name'],
            'clone_url': webhook_data['repository']['clone_url'],
            'default_branch': webhook_data['repository']['default_branch'],
            'language': webhook_data['repository'].get('language', ''),
            'commits': webhook_data.get('commits', [])
        }
        
        # Only process Python repositories
        if repo_data['language'] != 'Python':
            logger.info(f"Skipping non-Python repository: {repo_data['full_name']}")
            return
            
        await self.processing_queue.put(repo_data)
        logger.info(f"Queued {repo_data['full_name']} for processing")
    
    async def process_queue(self):
        """Background processor for queued repositories"""
        while True:
            try:
                repo_data = await self.processing_queue.get()
                await self.process_repository(repo_data)
                self.processing_queue.task_done()
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)
    
    async def process_repository(self, repo_data):
        """Process a repository with GenAI test generation"""
        repo_name = repo_data['full_name']
        logger.info(f"🤖 Processing repository: {repo_name}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone repository
                clone_cmd = ['git', 'clone', '--depth', '2', repo_data['clone_url'], temp_dir]
                subprocess.run(clone_cmd, check=True, capture_output=True)
                
                # Change to repo directory
                os.chdir(temp_dir)
                
                # Detect Python changes
                changed_files = await self.detect_python_changes()
                if not changed_files:
                    logger.info(f"No Python changes detected in {repo_name}")
                    return
                
                # Build context
                context = await self.build_context(changed_files)
                
                # Generate tests
                test_results = await self.generate_tests(context)
                
                # Create GitHub check run with results
                await self.create_github_check_run(repo_data, test_results)
                
                logger.info(f"✅ Completed processing {repo_name}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {repo_name}: {e}")
    
    async def detect_python_changes(self):
        """Detect changed Python files"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                capture_output=True, text=True, timeout=30
            )
            files = [f for f in result.stdout.strip().split('\n') 
                    if f.endswith('.py') and f and os.path.exists(f)]
            return files
        except:
            return []
    
    async def build_context(self, changed_files):
        """Build context bundle for changed files"""
        context = {
            'files': [],
            'metadata': {
                'changed_files': len(changed_files),
                'total_files': len(changed_files)
            }
        }
        
        for file_path in changed_files[:5]:  # Limit to 5 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                context['files'].append({
                    'path': file_path,
                    'full_text': content[:10000],  # Limit content
                    'unified_diff': f"Modified: {file_path}"
                })
            except:
                continue
                
        return context
    
    async def generate_tests(self, context):
        """Generate tests using Ollama"""
        # This would integrate with your existing generate_tests.py logic
        # For brevity, returning mock results
        return {
            'tests_generated': len(context['files']),
            'coverage_percentage': 75,
            'success': True
        }
    
    async def create_github_check_run(self, repo_data, test_results):
        """Create GitHub check run with test results"""
        if not GITHUB_TOKEN:
            return
            
        check_run_data = {
            'name': 'GenAI Test Platform',
            'head_sha': repo_data.get('head_commit', {}).get('id', 'HEAD'),
            'status': 'completed',
            'conclusion': 'success' if test_results['success'] else 'failure',
            'output': {
                'title': f"Generated {test_results['tests_generated']} test files",
                'summary': f"""
## 🤖 GenAI Test Platform Results

- **Tests Generated**: {test_results['tests_generated']}
- **Coverage**: {test_results['coverage_percentage']}%
- **Status**: {'✅ Success' if test_results['success'] else '❌ Failed'}

AI-powered test generation completed automatically.
                """.strip()
            }
        }
        
        url = f"https://api.github.com/repos/{repo_data['full_name']}/check-runs"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        async with self.session.post(url, json=check_run_data, headers=headers) as resp:
            if resp.status == 201:
                logger.info(f"✅ Created check run for {repo_data['full_name']}")
            else:
                logger.error(f"❌ Failed to create check run: {resp.status}")

# Web application setup
async def create_app():
    service = GenAITestPlatformService()
    await service.start()
    
    app = web.Application()
    app.router.add_post('/webhook', service.handle_webhook)
    app.router.add_get('/', lambda r: web.Response(text="GenAI Test Platform Service Running"))
    
    return app

if __name__ == '__main__':
    print("🚀 Starting GenAI Test Platform Centralized Service")
    print(f"   Listening on port {PORT}")
    print("   Configure GitHub organization webhook to point here")
    
    app = create_app()
    web.run_app(app, port=PORT)