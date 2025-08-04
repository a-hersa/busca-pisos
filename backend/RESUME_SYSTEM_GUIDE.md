# Municipios Spider Resume System

This document explains the resume system implemented for the municipios spider to handle interruptions gracefully.

## Features

### 1. **Automatic State Management**
- Tracks processed page count and last processed URL
- Saves checkpoints every 50 processed pages
- Preserves state on interruption (CTRL+C, quota exhaustion, system shutdown)
- Automatically cleans state files on successful completion

### 2. **Graceful Shutdown**
- **CTRL+C Detection**: Signal handlers catch interrupts and save state
- **Quota Exhaustion**: Middleware detects ScrapingAnt quota limits and triggers graceful shutdown
- **Pending URL Preservation**: Saves unprocessed URLs from scheduler queue

### 3. **Intelligent Resume**
- Automatically detects if previous crawl was interrupted
- Resumes from exact point of interruption
- Validates state file age (ignores states older than 7 days)
- Distinguishes between completed vs interrupted crawls

## Files Created

### State Files (in `./scraping/crawls/municipios/`)
- `spider_state.pkl` - Main state (processed count, last URL, reason for closure)
- `pending_urls.pkl` - URLs that were queued but not processed
- `checkpoint.pkl` - Periodic progress checkpoints

## How It Works

### Fresh Start
```bash
# No state files exist - starts normally from start_urls
scrapy crawl municipios
```

### Resume After Interruption
```bash
# State files exist from interrupted crawl - resumes automatically
scrapy crawl municipios
```

### Quota Exhaustion Scenario
1. ScrapingAnt returns 403 with "quota limit reached"
2. Middleware detects quota message and sets `spider.quota_exhausted = True`
3. Spider closes with reason `quota_exhausted`
4. All current state and pending URLs are saved
5. Next run will automatically resume from interruption point

### Manual Interruption (CTRL+C)
1. Signal handler catches SIGINT/SIGTERM
2. Spider closes with reason `user_interrupt`  
3. State and pending URLs are preserved
4. Next run resumes from interruption point

### Successful Completion
1. Spider completes normally with reason `finished`
2. All state files are automatically cleaned
3. Next run starts fresh from beginning

## State File Contents

### spider_state.pkl
```python
{
    'reason': 'quota_exhausted',          # Why spider closed
    'processed_count': 1250,              # Pages processed
    'last_processed_url': 'https://...',  # Last URL processed
    'timestamp': 1690834567.123,          # Unix timestamp
    'start_time': 1690834000.456,         # When crawl started
    'quota_exhausted': True               # Quota status
}
```

### pending_urls.pkl
```python
[
    'https://www.idealista.com/venta-viviendas/madrid/',
    'https://www.idealista.com/venta-viviendas/barcelona/',
    # ... more URLs that were queued but not processed
]
```

## Benefits

✅ **Zero Data Loss** - No re-crawling of already processed pages  
✅ **Cost Efficient** - Preserves ScrapingAnt API quota  
✅ **Fault Tolerant** - Handles system crashes, network issues, quota limits  
✅ **User Friendly** - Automatic detection and resume, no manual intervention needed  
✅ **Clean State** - Auto-cleanup prevents stale state accumulation  

## Usage Examples

### Check Resume Status
```bash
# Look for state files
ls -la ./scraping/crawls/municipios/

# If spider_state.pkl exists, next run will resume
# If no state files, next run starts fresh
```

### Force Fresh Start
```bash
# Remove state files to force fresh start
rm -f ./scraping/crawls/municipios/spider_state.pkl
rm -f ./scraping/crawls/municipios/pending_urls.pkl
rm -f ./scraping/crawls/municipios/checkpoint.pkl

# Now run spider - will start from beginning
scrapy crawl municipios
```

### Monitor Progress
Check spider logs for messages like:
```
[municipios] INFO: Resuming from previous interrupted crawl
[municipios] INFO: Loaded state: 1250 pages processed, last URL: https://...
[municipios] INFO: Resuming with 847 pending URLs
[municipios] INFO: Progress: 1300 pages processed, 23 URLs discovered from this page
```

## Implementation Details

The resume system is implemented entirely within Scrapy components:

- **Spider** (`municipios.py`) - State tracking, signal handling, resume logic
- **Middleware** (`middlewares.py`) - Quota detection and graceful shutdown
- **No external dependencies** - Uses only Python stdlib and Scrapy features

This ensures the system is lightweight, reliable, and doesn't interfere with existing FastAPI/Celery infrastructure.