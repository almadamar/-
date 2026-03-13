async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    """إرسال ملف النشاط وحذفه بعد 10 دقائق"""
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        try:
            with open(LOG_FILE, "rb") as document:
                # إرسال التقرير وحفظ معلومات الرسالة المرسلة في متغير sent_msg
                sent_msg = await context.bot.send_document(
                    chat_id=OWNER_ID,
                    document=document,
                    filename=f"Report_{datetime.now().strftime('%Y-%m-%d')}.txt",
                    caption=f"📅 تقرير النشاط اليومي\n⏰ تم الإرسال في: {datetime.now().strftime('%H:%M')}\n⚠️ سيتم حذف هذه الرسالة تلقائياً بعد 10 دقائق."
                )
            
            # مسح الملف من السيرفر لبدء يوم جديد
            os.remove(LOG_FILE)
            print("✅ تم إرسال التقرير وتصفير السجل.")

            # جدولة عملية الحذف بعد 600 ثانية (10 دقائق)
            # نمرر آيدي الرسالة وآيدي الدردشة للدالة المسؤولة عن الحذف
            context.job_queue.run_once(
                delete_report_msg, 
                when=600, 
                data={"chat_id": OWNER_ID, "message_id": sent_msg.message_id}
            )

        except Exception as e:
            print(f"❌ خطأ في إرسال التقرير اليومي: {e}")
    else:
        print("ℹ️ لا يوجد نشاط لإرساله اليوم.")

async def delete_report_msg(context: ContextTypes.DEFAULT_TYPE):
    """دالة مساعدة لحذف رسالة التقرير"""
    job_data = context.job.data
    try:
        await context.bot.delete_message(
            chat_id=job_data["chat_id"], 
            message_id=job_data["message_id"]
        )
        print("🗑️ تم حذف تقرير الـ 10 دقائق من المحادثة بنجاح.")
    except Exception as e:
        print(f"❌ لم يتمكن البوت من حذف الرسالة: {e}")
