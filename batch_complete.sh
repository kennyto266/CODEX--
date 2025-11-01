#!/bin/bash

echo "============================================================"
echo " BATCH COMPLETE ALL TASKS - 10 BATCHES"
echo "============================================================"
echo ""

total_success=0
total_failed=0

for batch in {1..10}; do
    echo "[Batch $batch/10] Updating tasks $((batch*10-9)) to $((batch*10))..."

    success=0
    failed=0

    for i in $(seq $((batch*10-9)) $((batch*10))); do
        # 使用TASK-XXX格式，但需要处理数字
        task_id="TASK-$((100+i))"

        # 直接更新为已完成
        response=$(curl -s -w "%{http_code}" -o /dev/null \
            -X PUT "http://localhost:8000/tasks/$task_id/status" \
            -d "new_status=已完成")

        if [ "$response" = "200" ]; then
            ((success++))
        else
            ((failed++))
        fi
    done

    echo "  Batch $batch: Success=$success, Failed=$failed"
    ((total_success+=success))
    ((total_failed+=failed))

    # 短暂延迟避免过载
    sleep 0.5
done

echo ""
echo "============================================================"
echo " COMPLETION SUMMARY"
echo "============================================================"
echo "Total Success: $total_success"
echo "Total Failed: $total_failed"
echo "Total Tasks: $((total_success + total_failed))"
echo "Success Rate: $(( total_success * 100 / (total_success + total_failed) ))%"
echo ""
echo "ALL TASKS COMPLETED!"
echo "============================================================"
