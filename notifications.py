"""Durable outbox; no complaint text or tracking secrets in email. Retry explicitly."""
import os,smtplib,ssl
from email.message import EmailMessage
from sqlalchemy import select,update
from .store import Notification,Grievance

def dispatch(session_factory):
    with session_factory() as s:
        ids=list(s.scalars(select(Notification.id).where(Notification.delivery=='pending').limit(100)))
    for ident in ids:
        with session_factory() as s:
            # Claim atomically so concurrent submission tasks cannot send twice.
            claim=s.execute(update(Notification).where(Notification.id==ident,Notification.delivery=='pending').values(delivery='sending'))
            s.commit()
            if not claim.rowcount:continue
            n=s.get(Notification,ident);g=s.get(Grievance,n.grievance_id);n.attempts+=1
            if not g.email or os.getenv('EMAIL_ENABLED','false').lower()!='true':n.delivery='local';s.commit();continue
            try:
                msg=EmailMessage();msg['Subject']='Grievance status update';msg['From']=os.environ['SMTP_FROM'];msg['To']=g.email;msg.set_content(n.message)
                with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.getenv('SMTP_PORT','587')),timeout=10) as smtp:
                    smtp.starttls(context=ssl.create_default_context())
                    if os.getenv('SMTP_USER'):smtp.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD'])
                    smtp.send_message(msg)
                n.delivery='sent'
            except Exception:n.delivery='failed'
            s.commit()
