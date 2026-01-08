#!/usr/bin/env python3
import subprocess
import json
import os
from datetime import datetime
from collections import defaultdict

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

def check_single_url(url):
    """Run lychee on a single URL and parse the output"""
    full_url = f"https://{url}"
    
    # Run lychee with detailed output
    result = subprocess.run(
        [
            'lychee', 
            '--verbose',
            '--no-progress',
            '--format', 'detailed',
            '--exclude-mail',
            '--timeout', '20',
            '--max-retries', '3',
            full_url
        ],
        capture_output=True,
        text=True
    )
    
    # Parse the output for broken links
    broken_links = []
    lines = result.stdout.split('\n')
    
    for i, line in enumerate(lines):
        if '[ERROR]' in line or '[BROKEN]' in line or '✗' in line:
            # Extract the URL and status
            parts = line.split()
            for part in parts:
                if part.startswith('http'):
                    # Look for status code in nearby lines
                    status = 'Unknown'
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        if 'Status:' in lines[j] or '│' in lines[j]:
                            status_parts = lines[j].split()
                            for k, sp in enumerate(status_parts):
                                if sp.isdigit() and len(sp) == 3:
                                    status = sp
                                    break
                    
                    broken_links.append({
                        'url': part.strip('│').strip(),
                        'status': status
                    })
                    break
    
    return {
        'parent_url': full_url,
        'broken_links': broken_links,
        'exit_code': result.returncode,
        'full_output': result.stdout + '\n' + result.stderr
    }

def main():
    """Check all URLs and generate reports"""
    os.makedirs('results', exist_ok=True)
    
    # Store all results
    all_results = []
    urls_with_broken_links = []
    total_broken_links = 0
    detailed_output = []
    
    print(f"Checking {len(URLS)} URLs for broken links...")
    
    for i, url in enumerate(URLS, 1):
        print(f"[{i}/{len(URLS)}] Checking {url}...")
        result = check_single_url(url)
        all_results.append(result)
        
        if result['broken_links']:
            urls_with_broken_links.append(result)
            total_broken_links += len(result['broken_links'])
        
        # Store detailed output
        detailed_output.append(f"\n{'='*80}")
        detailed_output.append(f"URL: {result['parent_url']}")
        detailed_output.append(f"{'='*80}")
        detailed_output.append(result['full_output'])
    
    # Save detailed output
    with open('results/detailed-lychee-output.txt', 'w') as f:
        f.write('\n'.join(detailed_output))
    
    # Generate JSON report
    json_report = {
        'scan_date': datetime.now().isoformat(),
        'total_urls_scanned': len(URLS),
        'urls_with_broken_links': len(urls_with_broken_links),
        'total_broken_links': total_broken_links,
        'results': urls_with_broken_links
    }
    
    with open('results/link-report.json', 'w') as f:
        json.dump(json_report, f, indent=2)
    
    # Generate markdown report
    generate_markdown_report(urls_with_broken_links, len(URLS), total_broken_links)

        # Exit with error if broken links found
    if urls_with_broken_links:
        print(f"\n❌ Found {total_broken_links} broken links across {len(urls_with_broken_links)} pages")
        exit(1)
    else:
        print("\n✅ No broken links found!")
        exit(0)

def generate_markdown_report(results, total_urls, total_broken):
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
        report.append("## ❌ Broken Links by Page\n")
        
        # Group broken links by status code
        status_summary = defaultdict(int)
        
        for result in results:
            parent_url = result['parent_url']
            broken_links = result['broken_links']
            
            report.append(f"### 📄 {parent_url}")
            report.append(f"**Broken links found:** {len(broken_links)}\n")
            
            # Group by status for better readability
            by_status = defaultdict(list)
            for link in broken_links:
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
    report.append("*For detailed output, check the workflow artifacts.*")
    
    # Save report
    with open('results/link-report.md', 'w') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Markdown report generated: results/link-report.md")

if __name__ == "__main__":
    main()