# How to Check Elastic Beanstalk Logs

## Method 1: EB Console (Easiest)

1. **Go to AWS Elastic Beanstalk Console**
   - https://console.aws.amazon.com/elasticbeanstalk/

2. **Select your environment**

3. **Go to Logs** (left sidebar)

4. **Click "Request Logs"** → **"Last 100 Lines"**
   - This shows recent log entries
   - Look for errors related to your deployment

5. **Or click "Full Logs"** → **"Download"**
   - Downloads a zip file with all logs
   - Extract and look for `var/log/eb-engine.log`

## Method 2: EB Console - Log Streaming

1. **Go to your environment**

2. **Click "Logs"** → **"Request Logs"**

3. **Select "Instance Logs"** tab

4. **Look for:**
   - `eb-engine.log` - Deployment engine logs
   - `eb-hooks.log` - Hook execution logs (this is where our prebuild hook output will be)
   - `eb-activity.log` - General activity logs

## Method 3: Using EB CLI (Command Line)

If you have EB CLI installed:

```bash
# View recent logs
eb logs

# Download logs
eb logs --all

# View specific log file
eb logs | grep -A 50 "eb-engine.log"
```

## Method 4: SSH into Instance (Advanced)

1. **Enable SSH access:**
   - EB Console → Configuration → Security → EC2 key pair
   - Add your EC2 key pair

2. **SSH into instance:**
   ```bash
   ssh ec2-user@your-instance-ip
   ```

3. **View logs:**
   ```bash
   # eb-engine.log
   sudo tail -100 /var/log/eb-engine.log
   
   # eb-hooks.log (our prebuild hook output)
   sudo tail -100 /var/log/eb-hooks.log
   
   # Full log
   sudo cat /var/log/eb-engine.log
   ```

## What to Look For

In the logs, look for:

1. **Our prebuild hook output:**
   ```
   === Frontend Build Hook Started ===
   ```

2. **Error messages:**
   - "node command not found"
   - "npm install failed"
   - "npm run build failed"
   - Any exit codes or error messages

3. **Deployment errors:**
   - "Command failed"
   - "Instance deployment failed"
   - Any stack traces

## Quick Check - Most Common Location

**Easiest way:**
1. EB Console → Your Environment
2. **Logs** → **Request Logs** → **Last 100 Lines**
3. Look for error messages (they're usually at the top)

## Screenshot Guide

1. Open EB Console
2. Click on your environment name
3. Click **"Logs"** in the left sidebar
4. Click **"Request Logs"**
5. You'll see:
   - **Last 100 Lines** - Quick view
   - **Full Logs** - Download all logs
   - **Instance Logs** - View specific log files

The error from your deployment should be visible in "Last 100 Lines" or in the downloaded logs under `var/log/eb-engine.log` or `var/log/eb-hooks.log`.

