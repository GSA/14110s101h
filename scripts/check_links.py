#!/usr/bin/env python3
import subprocess
import json
import os
from datetime import datetime
from collections import defaultdict
import re

# Static list of URLs
URLS = [
    "gsa.gov/node/125239", "gsa.gov/node/93921", "gsa.gov/node/149227",
    "gsa.gov/node/156884", "gsa.gov/node/108063", "gsa.gov/node/164959",
    "gsa.gov/node/84385", "gsa.gov/node/84255", "gsa.gov/node/162818",
    "gsa.gov/node/87101", "gsa.gov/node/165727", "gsa.gov/node/160304",
    "gsa.gov/node/91065", "gsa.gov/node/85818", "gsa.gov/node/87099",
    "gsa.gov/node/87291", "gsa.gov/node/87273", "gsa.gov/node/87318",
    "gsa.gov/node/87027", "gsa.gov/node/87324", "gsa.gov/node/87632",
    "gsa.gov/node/87730", "gsa.gov/node/87591", "gsa.gov/node/87566",
    "gsa.gov/node/86906", "gsa.gov/node/90877", "gsa.gov/node/162789",
    "gsa.gov/node/162790", "gsa.gov/node/87293", "gsa.gov/node/86610",
    "gsa.gov/node/87728", "gsa.gov/node/84227", "gsa.gov/node/85145",
    "gsa.gov/node/87265", "gsa.gov/node/162854", "gsa.gov/node/162786",
    "gsa.gov/node/162856", "gsa.gov/node/98938", "gsa.gov/node/98940",
    "gsa.gov/node/84639", "gsa.gov/node/139949", "gsa.gov/node/162791",
    "gsa.gov/node/162849", "gsa.gov/node/84516", "gsa.gov/node/165911",
    "gsa.gov/node/128482", "gsa.gov/node/162828", "gsa.gov/node/162826",
    "gsa.gov/node/257", "gsa.gov/node/87387", "gsa.gov/node/84613",
    "gsa.gov/node/87680", "gsa.gov/node/84432", "gsa.gov/node/149831"
]

def run_lychee_properly(urls):
    """Run lychee on all URLs to check links WITHIN those pages"""
    # Create a temporary file with all URLs
    urls_content = '\n'.join([f"https://{url}" for url in urls])
    
    # Run lychee with --max-depth to crawl the pages
    cmd = [
        'lychee', 
        '--verbose', 
        '--no-progress',
        '--max-depth', '1',  # This tells lychee to check links ON the pages
        '--format', 'json',
        '--exclude', '^mailto:',
        '--exclude', '^tel:',
        '--exclude', '^javascript:',
        '-'
    ]
    
    result = subprocess.run(
        cmd,
        input=urls_content,
        capture_output=True,
        text=True
    )
    
    return result

def parse_lychee_output(output):
    """Parse lychee's verbose output to extract broken links by parent URL"""
    results_by_url = defaultdict(list)
    current_url = None
    
    lines = output.split('\n')
    
    for i, line in enumerate(lines):
        # Look for URL being checked
        if line.strip().startswith('https://gsa.gov/node/'):
            current_url = line.strip()
            continue
        
        # Look for broken links (various formats lychee might use)
        # Format 1: [404] https://example.com/broken
        # Format 2: ✗ https://example.com/broken (404 Not Found)
        # Format 3: │ https://example.com/broken │ 404 │
        
        # Check for 404 or other error status codes
        if current_url and ('404' in line or '403' in line or '500' in line or '502' in line or '503' in line or '[4' in line or '[5' in line or '✗' in line):
            # Extract URL from the line
            url_match = re.search(r'https?://[^\s\│\]]+', line)
            if url_match:
                broken_url = url_match.group(0).strip()
                
                # Extract status code
                status_match = re.search(r'[45]\d{2}', line)
                status = status_match.group(0) if status_match else 'Unknown'
                
                # Don't add the parent URL as a broken link
                if broken_url != current_url:
                    results_by_url[current_url].append({
                        'url': broken_url,
                        'status': status
                    })
    
    return results_by_url

def main():
    """Check all URLs and generate reports"""
    os.makedirs('results', exist_ok=True)
    
    print(f"Running lychee on {len(URLS)} URLs...")
    
    # Run lychee on all URLs
    result = run_lychee_properly(URLS)
    
    # Save raw output for debugging
    with open('results/detailed-lychee-output.txt', 'w') as f:
        f.write("=== LYCHEE FULL OUTPUT ===\n")
        f.write(f"Command: lychee --verbose --no-progress -\n")
        f.write(f"Exit code: {result.returncode}\n")
        f.write("\n=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
    
    # Parse the output
    broken_links_by_url = parse_lychee_output(result.stdout + '\n' + result.stderr)
    
    # Filter out empty results
    urls_with_broken_links = []
    total_broken_links = 0
    
    # Track common broken links across multiple pages
    common_broken_links = defaultdict(list)
    
    for parent_url, broken_links in broken_links_by_url.items():
        if broken_links:
            urls_with_broken_links.append({
                'parent_url': parent_url,
                'broken_links': broken_links
            })
            total_broken_links += len(broken_links)
            
            # Track which pages have which broken links
            for link in broken_links:
                common_broken_links[link['url']].append(parent_url)
    
    # Generate JSON report
    json_report = {
        'scan_date': datetime.now().isoformat(),
        'total_urls_scanned': len(URLS),
        'urls_with_broken_links': len(urls_with_broken_links),
        'total_broken_links': total_broken_links,
        'results': urls_with_broken_links,
        'common_broken_links': {
            url: {
                'appears_on_pages': pages,
                'count': len(pages)
            }
            for url, pages in common_broken_links.items()
        }
    }
    
    with open('results/link-report.json', 'w') as f:
        json.dump(json_report, f, indent=2)
    
    # Generate markdown report
    generate_markdown_report(urls_with_broken_links, len(URLS), total_broken_links, common_broken_links)
    
    # Exit with error if broken links found
    if urls_with_broken_links:
        print(f"\n❌ Found {total_broken_links} broken links across {len(urls_with_broken_links)} pages")
        exit(1)
    else:
        print("\n✅ No broken links found!")
        exit(0)

def generate_markdown_report(results, total_urls, total_broken, common_links):
    """Generate a formatted markdown report"""
    report = []
    report.append("# 🔍 Link Checker Report")
    report.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append(f"**Total URLs Scanned:** {total_urls}")
    report.append(f"**URLs with Broken Links:** {len(results)}")
    report.append(f"**Total Broken Links Found:** {total_broken}\n")
    
    if not results:
        report.append("## ✅ No broken links found!")
        report.append("\nAll scanned pages have valid links.")
    else:
        # First, show common broken links (likely in navigation/menus)
        menu_links = {url: data for url, data in common_links.items() if data['count'] > 5}
        if menu_links:
            report.append("## 🔗 Common Broken Links (Likely in Menus/Navigation)\n")
            report.append("These broken links appear on many pages and are likely in shared navigation:")
            report.append("")
            
            for url, data in sorted(menu_links.items(), key=lambda x: x[1]['count'], reverse=True):
                report.append(f"- **{url}** (appears on {data['count']} pages)")
            report.append("")
        
        # Then show page-specific broken links
        report.append("## ❌ Broken Links by Page\n")
        
        # Group broken links by status code
        status_summary = defaultdict(int)
        
        for result in results:
            parent_url = result['parent_url']
            broken_links = result['broken_links']
            
            # Filter out common menu links for the detailed view
            page_specific_links = [
                link for link in broken_links 
                if common_links.get(link['url'], {}).get('count', 0) <= 5
            ]
            
            if page_specific_links:  # Only show if there are page-specific broken links
                report.append(f"### 📄 {parent_url}")
                report.append(f"**Page-specific broken links:** {len(page_specific_links)}")
                report.append(f"**Total broken links (including menu):** {len(broken_links)}\n")
                
                # Group by status for better readability
                by_status = defaultdict(list)
                for link in page_specific_links:
                    by_status[link['status']].append(link['url'])
                    status_summary[link['status']] += 1
                
                for status, urls in sorted(by_status.items()):
                    report.append(f"#### Status {status}:")
                    for url in urls:
                        report.append(f"- ❌ `{url}`")
                    report.append("")
        
        # Add summary section
        report.append("\n## 📊 Summary by Status Code\n")
        for status, count in sorted(status_summary.items()):
            report.append(f"- **{status}**: {count} links")
    
    # Add footer with helpful information
    report.append("\n---")
    report.append("*This report was automatically generated by the GSA Link Checker workflow.*")
    report.append("*Common broken links (appearing on many pages) are likely in shared navigation/menus.*")
    report.append("*For detailed output, check the workflow artifacts.*")
    
    # Save report
    with open('results/link-report.md', 'w') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Markdown report generated: results/link-report.md")

if __name__ == "__main__":
    main()