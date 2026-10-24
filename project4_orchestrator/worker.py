async def process_task(task_data: dict):
    """Executes the specific business/mathematical workload and tracks its state."""
    task_id = task_data.get("task_id")
    task_type = task_data.get("type")
    payload = task_data.get("payload", {})
    webhook_url = task_data.get("webhook_url")
    retries = task_data.get("retries", 0)

    # BULLETPROOF ENFORCEMENT: If the URL is broken, truncated, or pointing to port 80
    if "127.0.0.1" in webhook_url and "5001" not in webhook_url:
        webhook_url = "http://127.0.0.1:5001"

    logger.info(f"Processing Task {task_id} [{task_type}] - Attempt {retries + 1}")
    
    try:
        if task_type == "video_transcode":
            duration = payload.get("duration_sec", 2)
            await asyncio.sleep(duration)
            result = {"output_url": f"https://cdn.local{task_id}.mp4", "status": "COMPLETED"}
            
        elif task_type == "math_compute":
            numbers = payload.get("numbers", [])
            result = {"sum": sum(numbers), "product": eval("*".join(map(str, numbers)) if numbers else "0"), "status": "COMPLETED"}
            
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        callback_payload = {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": result,
            "timestamp": time.time()
        }
        await dispatch_webhook(webhook_url, callback_payload)

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        if retries < Config.MAX_RETRIES:
            task_data["retries"] = retries + 1
            logger.info(f"Scheduling Task {task_id} for retry in {Config.RETRY_DELAY_SEC}s...")
            await asyncio.sleep(Config.RETRY_DELAY_SEC)
            redis_client.lpush(Config.TASK_QUEUE_NAME, json.dumps(task_data))
        else:
            logger.error(f"Task {task_id} exceeded maximum retries. Hard failing.")
            callback_payload = {
                "task_id": task_id,
                "status": "FAILED",
                "error": str(e),
                "timestamp": time.time()
            }
            await dispatch_webhook(webhook_url, callback_payload)
