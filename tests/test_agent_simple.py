#!/usr/bin/env python3
"""Simple test script for agent functions."""

import sys
import os

# Add the project root to Python path (parent directory of tests/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.agent import (
    scrape_job_offerings,
    agent_search_blog_articles,
    get_latest_info,
    get_service_description,
    generate_chat_response
)

def test_scrape_jobs():
    """Test job scraping."""
    print("\n🧪 Testing Job Scraping...")
    jobs = scrape_job_offerings()
    
    if jobs and len(jobs) > 0:
        print(f"✅ Found {len(jobs)} job listing(s)")
        for job in jobs[:2]:  # Show first 2
            print(f"   - {job.get('title', 'N/A')}")
    else:
        print("⚠️  No jobs found")
    
    return jobs

def test_blog_search():
    """Test blog article search."""
    print("\n🧪 Testing Blog Article Search...")
    results = agent_search_blog_articles("AI marketing services")
    
    if results and len(results) > 0:
        print(f"✅ Found {len(results)} article(s)")
        for article in results[:2]:  # Show first 2
            print(f"   - {article.get('title', 'N/A')}")
    else:
        print("⚠️  No articles found")
    
    return results

def test_latest_info():
    """Test latest info retrieval."""
    print("\n🧪 Testing Latest Info Retrieval...")
    info = get_latest_info()
    
    if info and not info.get('error'):
        print(f"✅ Latest info loaded successfully")
        print(f"   Data keys: {list(info.keys())[:5]}")  # Show first 5 keys
    else:
        print(f"⚠️  Error: {info.get('error', 'Unknown error')}")
    
    return info

def test_service_description():
    """Test service description retrieval."""
    print("\n🧪 Testing Service Description...")
    services = get_service_description()
    
    if services:
        print(f"✅ Services loaded successfully")
        print(f"   Length: {len(services)} characters")
    else:
        print("⚠️  No services found")
    
    return services

def test_chat_response():
    """Test full chat response generation."""
    print("\n🧪 Testing Full Chat Response...")
    query = "What services does Neckarmedia offer?"
    
    try:
        response = generate_chat_response(query)
        if response:
            print(f"✅ Chat response generated successfully")
            print(f"   Response (first 200 chars): {response[:200]}...")
        else:
            print("⚠️  Empty response")
        return response
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 NECKARMEDIA AGENT TESTS")
    print("=" * 60)
    
    # Run all tests
    test_scrape_jobs()
    test_blog_search()
    test_latest_info()
    test_service_description()
    test_chat_response()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

