"""Monthly customer mailing."""

from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime, timedelta
from locale import LC_TIME, setlocale
from logging import basicConfig, getLogger
from pathlib import Path
from typing import Iterable, Iterator
from peewee import DoesNotExist

from emaillib import EMailsNotSent, EMail, Mailer
from hwdb import Deployment, System
from mdb import Customer

from his import ACCOUNT
from sysmon.config import get_config
from sysmon.mean_stats import MeanStats
from sysmon.orm import (
    CheckResults,
    UserNotificationEmail,
    ExtraUserNotificationEmail,
    Newsletter,
)


__all__ = ["main", "send_mailing", "get_newsletter_by_date", "send_test_mails"]


TEMPLATE = Path("/usr/local/etc/sysmon.d/customers-email.htt")
MAIL_START = """<html>
<style>h1,.h1{
  font-size: 60px !important;
  line-height: 66px !important;
}h2,.h2{
  font-size: 44px !important;
  line-height: 50px !important;
}.btn a:hover{
  background-color:#000000!important; 
  border-color:#000000!important;
}.textcta a:hover{
  color:#000000!important;
  }p {margin: 0 !important;}.divbox:hover, * [lang~="x-divbox"]:hover {
  background-color: #000000 !important;
}.boxfont:hover, * [lang~="x-boxfont"]:hover {
  color: #ffffff !important;
  
}
.bgcol{
background-color: #E9F0FF;
}
a {text-decoration: none;}a[x-apple-data-detectors] { color: inherit !important; text-decoration: none !important; font-size: inherit !important; font-family: inherit !important; font-weight: inherit !important; line-height: inherit !important }table{ mso-table-lspace: 0; mso-table-rspace: 0; mso-table-lspace: 0; border: none; border-collapse: collapse; border-spacing: 0;}p {margin: 0 !important;}h1, .h1, .h1l { font-size: 60px !important; line-height: 66px !important; }h2, .h2 { font-size: 44px !important; line-height: 50px !important; }ul, ol {margin:0; margin-left:8px !important;}u + .body ul, u + .body ol { margin-left: 8px !important; }.show670, .show414 {display:none;}sup { line-height:0; font-size:70%; }</style>

</head>


<body dir="ltr" style="-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%;background-color:#d6d6d5;margin:0;min-width:100%;padding:0;width:100%"><div class="moz-text-html" lang="x-unicode">


<table style="background-color:#d6d6d5;border:0;border-collapse:collapse;border-spacing:0;mso-table-lspace:0;mso-table-rspace:0" class="" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#d6d6d5">
<tbody>
<tr>
<td style="display: block;" align="center">
<!--[if (gte mso 9)|(IE)]>
<table width="700" align="center" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<![endif]-->
<table style="border:0;border-collapse:collapse;border-spacing:0;max-width:700px;mso-table-lspace:0;mso-table-rspace:0" class="" width="100%" cellspacing="0" cellpadding="0" border="0">
<tbody>
<tr>
<td style="background-color:#ffffff">




<table style="border: none; border-collapse: collapse; border-spacing: 0; mso-table-lspace: 0; mso-table-rspace: 0; width: 100%;"  width="100%" cellspacing="0" cellpadding="0" border="0">
  <tbody>
  <tr>
    <td class="outsidegutter bgcol" style=" direction: ltr; padding: 10px 14px 10px 14px; padding-left: 0; text-align: left;" align="left">

      <table style="border: none; border-collapse: collapse; border-spacing: 0; mso-table-lspace: 0; mso-table-rspace: 0; width: 100%;" class="" cellspacing="0" cellpadding="0" border="0">
      <tbody>
        <tr>
        <td style="direction:ltr;text-align:left;padding-left:0; padding-right:0;" width="14">
        </td>

        <td style="direction:ltr;text-align:left; font-size:0; ">


  <table  style="border: none; border-collapse: collapse; border-spacing: 0; display: inline-block; max-width: 616px; mso-table-lspace: 0; mso-table-rspace: 0; vertical-align: middle; width: 100%;" cellspacing="0" cellpadding="0" border="0">
    <tbody>
      <tr>
      <td style="direction:ltr;text-align:left;padding-left: 0; padding-right: 0;">
      <table style="border: none; border-collapse: collapse; border-spacing: 0; mso-table-lspace: 0; mso-table-rspace: 0; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
        <tbody>
          <tr>
            <td style="direction:ltr;text-align:left;font-size:0;">


              <table class="t4of12" style="border: none; border-collapse: collapse; border-spacing: 0; display: inline-block; max-width: 408px; mso-table-lspace: 0; mso-table-rspace: 0; vertical-align: middle; width: 100%;" cellspacing="0" cellpadding="0" border="0">
                <tbody>
                  <tr>
                  <td style="direction:ltr;text-align:left;padding-left: 12px; padding-right: 12px;">
                      <table style="border: none; border-collapse: collapse; border-spacing: 0; mso-table-lspace: 0; mso-table-rspace: 0; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
                        <tbody>



                    
                      <tr>
                        <td style="direction:ltr;text-align: left;">
						<h1>Homeinfo</h1>
    </td>
                      </tr>


                  

                  </tbody>

</table>
</td>
</tr>
</tbody></table>



</td>
</tr>
</tbody></table>
</td>
</tr>
</tbody></table>
<!--[if (gte mso 9)|(IE)]>
</td>
</tr>
</table>
<![endif]-->
</td>
</tr>
</tbody></table>
</td>
</tr>



</tbody></table> 
<table style="border: none; border-collapse: collapse; mso-table-lspace: 0; mso-table-rspace: 0; width: 100%;"  width="100%" cellspacing="0" cellpadding="0" border="0">
  <tbody><tr>
     <td class="" style="direction:ltr;text-align:left;" align="left">
<table style="border: none; border-collapse: collapse; mso-table-lspace: 0; mso-table-rspace: 0; width: 100%;" class="" cellspacing="0" cellpadding="0" border="0">
           <tbody><tr>
             

      <td class="bgcol">





 


<table style="border: none; border-collapse: collapse; mso-table-lspace: 0; mso-table-rspace: 0; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0">
  <tbody><tr>
    <td style="direction:ltr;text-align:left;" width="14">&nbsp;</td>
     <td class="xoutsidegutter" style="direction:ltr;text-align:left;" align="left">
        <table style="border: none; border-collapse: collapse; mso-table-lspace: 0; mso-table-rspace: 0; width: 100%;" class="" cellspacing="0" cellpadding="0" border="0">
           <tbody><tr>
              <td align="center">

<!--[if mso]></td>
<td valign="top">
  <![endif]-->


<!--[if (gte mso 9)|(IE)]>
<table width="616" align="left" cellpadding="0" cellspacing="0" border="0">
  <tr>
     <td>
        <![endif]-->
        <table class="t11of12 layout" style="border-collapse: collapse; max-width: 616px; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="left">
           <tbody><tr>
              <td style="direction:ltr;text-align:left;font-size: 1px; height: 1px; line-height: 1px; padding-left: 0px !important; padding-right: 0px !important; padding-top: 0px;">
                 <table style="border-collapse: collapse; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
                    <tbody><tr>
                       <td style="direction:ltr;text-align:left;" valign="top">
                         

<!--[if (gte mso 9)|(IE)]>
<table width="100%" align="left" cellpadding="0" cellspacing="0" border="0">
  <tr>
     <td valign="top">
        <![endif]-->
        <table class="t10of12 layout" style="border-collapse: collapse;  width: 100%;" cellspacing="0" cellpadding="0" border="0" align="left">
           <tbody><tr>
            <td style="direction:ltr;text-align:left;font-size: 1px; height: 1px; line-height: 1px; padding-left: 0px !important; padding-right: 0px !important;" width="12">&nbsp;</td>
              <td style="direction:ltr;text-align:left;font-size: 1px; height: 1px; line-height: 1px; padding-left: 0px !important; padding-right: 0px !important; padding-top: 0px; padding-bottom: 25px;">
                 <table style="border-collapse: collapse; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
                    

<tbody><tr>
  <td style="direction:ltr;text-align:left;">

<!--[if (gte mso 9)|(IE)]>
<table width="504" align="left" cellpadding="0" cellspacing="0" border="0">
  <tr>
     <td>
        <![endif]-->
        <table class="t9of12 layout" style="border-collapse: collapse; max-width: 504px; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="left">
           <tbody><tr>
              <td style="direction:ltr;text-align:left;font-size: 1px; height: 1px; line-height: 1px; padding-left: 0px !important; padding-right: 0px !important;">
                 <table style="border-collapse: collapse; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
                    <tbody>

                     



                     <tr>
                      <td class="h2_h2 h2" style="direction:ltr;text-align:left;color: #000000; font-family: Helvetica, Arial, sans-serif; font-size: 34px; font-weight: 500; line-height: 40px; padding-bottom: 7px; padding-top: 0px;">{header}
</td>
                     </tr>








                 </tbody></table>
              </td>
           </tr>
        </tbody></table>
        <!--[if (gte mso 9)|(IE)]>
     </td>
  </tr>
</table>
<![endif]-->  


  </td>
</tr>



                    <tr>
                     <td style="direction:ltr;text-align:left;padding-bottom: 20px">
<!--[if (gte mso 9)|(IE)]>
<table width="504" align="left" cellpadding="0" cellspacing="0" border="0">
  <tr>
     <td>
        <![endif]-->
        <table class="t6of12 layout" style="border-collapse: collapse; max-width: 504px; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="left">
           <tbody><tr>
              <td style="direction:ltr;text-align:left;font-size: 1px; height: 1px; line-height: 1px; padding-left: 0px !important; padding-right: 0px !important;">
                 <table style="border-collapse: collapse; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
                    <tbody>


                      <tr>
                       <td class="p1" style="direction:ltr;text-align:left;color: #000000; font-family: Helvetica, Arial, sans-serif; font-size: 20px; font-weight: normal; line-height: 26px; padding-bottom: 7px; padding-top: 7px;"><div>{text}</div>
</td>
                    </tr>





                 </tbody></table>
              </td>
           </tr>
        </tbody></table>
        <!--[if (gte mso 9)|(IE)]>
     </td>
  </tr>
</table>
<![endif]-->                        
                     </td>
                    </tr>
                    <tr>
                     <td style="direction:ltr;text-align:left;">
<!--[if (gte mso 9)|(IE)]>
<table width="250" align="left" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<![endif]-->
   <div class="btn" style="font-family: Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 700; line-height: 22px;" lang="x-btn"> <a href=""  style="background-color: #000000; border-color: #000000; border-radius: 0px; border-style: solid; border-width: 13px 18px; color: #ffffff; display: inline-block; letter-spacing: 1px; max-width: 300px; min-width: 100px; text-align: center; text-decoration: none; transition: all 0.2s ease-in;"><span style="float:left;text-align:left;">{merhlesen}</span> 
   <!--[if !mso]><!-- -->
   <!--<![endif]--> 
   </a> </div>
<!--[if (gte mso 9)|(IE)]>
</td>
</tr>
</table>
<![endif]-->                        
                     </td>
                    </tr>
                 </tbody></table>
              </td>
              <td style="direction:ltr;text-align:left;font-size: 1px; height: 1px; line-height: 1px; padding-left: 0px !important; padding-right: 0px !important;" width="12">&nbsp;</td>
           </tr>
        </tbody></table>
        <!--[if (gte mso 9)|(IE)]>
     </td>
  </tr>
</table>
<![endif]-->






                       </td>
                    </tr>
                 </tbody></table>
              </td>
           </tr>
        </tbody></table>
        <!--[if (gte mso 9)|(IE)]>
     </td>
  </tr>
</table>
<![endif]-->


              </td>
           </tr>
        </tbody></table>
     </td>
     <td style="direction:ltr;text-align:left;" width="14">&nbsp;</td>
  </tr>
</tbody></table>            


  <div class="hide414">
    <img class="hide414" src="{image}" style="-ms-interpolation-mode: bicubic; clear: both; display: block; height: auto; max-width: 700px; outline: none; text-decoration: none; width: 100%;" alt="" width="700" height="" border="0">
  </div>







             </td>
           </tr>
        </tbody></table>
     </td>
  </tr>
</tbody></table>
"""

MAIL_END = """</td>
</tr>
</tbody>
</table>
<!--[if (gte mso 9)|(IE)]>
</td>
</tr>
</table>
<![endif]-->
</td>
</tr>
</tbody>
</table>


</div></body>

</html>
"""

DDB_TEXT = """<p>Hiermit erhalten Sie einen Statusbericht für den Monat {month} {year} Ihrer Digitalen Bretter:<br>
Im Monat {month} waren {percent_online}% Ihrer Digitalen Bretter online.
</p>
<p>
Sofern sich dazu im Vorfeld Fragen ergeben, stehen wir Ihnen natürlich wie gewohnt sehr gern zur Verfügung.<br>
Bitte nutzen Sie den Link zur detaillierten Monatsstatistik. Hier werden Ihnen auch weiterführende Abläufe beschrieben:<br>
<a href="https://typo3.homeinfo.de/ddb-report?customer={customer.id}">Link zur Webansicht</a>
</p>"""
LOGGER = getLogger("sysmon-mailing")

FOOTER_TEXT = """ """


def main() -> None:
    """Main function for script invocation."""

    basicConfig()

    try:
        send_mailing()
    except EMailsNotSent as not_sent:
        for email in not_sent.emails:
            LOGGER.error("Email not sent: %s", email)


def send_mailing() -> None:
    """Send the mailing."""

    setlocale(LC_TIME, "de_DE.UTF-8")
    """ Send email for extra Users"""
    newsletter = get_newsletter_by_date(date.today())

    get_mailer().send(create_other_test_emails(newsletter.id))

    """ Send emails for DDB Clients"""
    get_mailer().send(
        list(
            create_emails_for_customers(
                get_target_customers(), last_day_of_last_month(date.today())
            )
        )
    )


def send_test_mails(newsletter: int):
    get_mailer().send(
        [create_customer_test_email(newsletter, ACCOUNT.customer, ACCOUNT.email)]
    )
    get_mailer().send([create_other_test_email(newsletter, ACCOUNT.email)])


def create_other_test_emails(newsletter: int):
    for email in ExtraUserNotificationEmail.select():
        yield create_other_test_email(newsletter, email.email)


def create_other_test_email(newsletter: int, recipient: str):
    """Creates a Mail for non DDB clients"""
    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )

    html = get_html_other(
        get_newsletter_by_date(
            Newsletter.select().where(Newsletter.id == newsletter).get().period
        ).text
    )

    return EMail(
        subject=get_newsletter_by_date(
            Newsletter.select().where(Newsletter.id == newsletter).get().period
        ).subject,
        sender=sender,
        recipient=recipient,
        html=html,
    )


def create_customer_test_email(newsletter: int, customer: Customer, recipient: str):
    """Creates a Mail for DDB clients"""
    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )
    last_month = last_day_of_last_month(date.today())
    if not (
        check_results := check_results_by_system(
            get_check_results_for_month(customer, last_month)
        )
    ):
        html = get_html_other(
            get_newsletter_by_date(
                Newsletter.select().where(Newsletter.id == newsletter).get().period
            ).text
        )
    else:
        html = get_html(
            get_newsletter_by_date(
                Newsletter.select().where(Newsletter.id == newsletter).get().period
            ).text,
            customer,
            MeanStats.from_system_check_results(check_results),
            last_month,
        )

    return EMail(
        subject=get_newsletter_by_date(
            Newsletter.select().where(Newsletter.id == newsletter).get().period
        ).subject,
        sender=sender,
        recipient=recipient,
        html=html,
    )


def get_target_customers() -> set[Customer]:
    """Yield customers that shall receive the mailing."""

    customers = set()

    for system in System.select(cascade=True).where(~(System.deployment >> None)):
        customers.add(system.deployment.customer)

    return customers


def get_mailer() -> Mailer:
    """Return the mailer."""

    return Mailer.from_config(get_config())


def get_newsletter_by_date(now) -> Newsletter:
    """Returns Newsletter for current year/month"""

    try:
        nl = (
            Newsletter.select()
            .where(
                (Newsletter.period.month == now.month)
                & (Newsletter.period.year == now.year)
                & (Newsletter.visible == 1)
            )
            .get()
        )
    except DoesNotExist:
        return Newsletter.select().where(Newsletter.isdefault == 1).get()
    return nl


def create_emails_for_customers(
    customers: Iterable[Customer], last_month: date
) -> Iterator[EMail]:
    """Create monthly notification emails for the given customers."""

    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )

    for customer in customers:
        yield from create_customer_emails(
            customer, sender=sender, last_month=last_month
        )


def create_customer_emails(
    customer: Customer, sender: str, last_month: date
) -> Iterator[EMail]:
    """Create the system status summary emails for the given month."""
    now = date.today()
    if not (
        check_results := check_results_by_system(
            get_check_results_for_month(customer, last_month)
        )
    ):
        html = get_html_other(get_newsletter_by_date(now).text)
    else:
        html = get_html(
            get_newsletter_by_date(now).text,
            customer,
            MeanStats.from_system_check_results(check_results),
            last_month,
        )

    for recipient in get_recipients(customer):
        yield EMail(
            subject=get_newsletter_by_date(now).subject,
            sender=sender,
            recipient=recipient,
            html=html,
        )


def get_html(
    body_text: str, customer: Customer, stats: MeanStats, last_month: date
) -> str:
    """Return the email body's for DDB customers."""
    template = MAIL_START + MAIL_END
    return template.format(
        month=last_month.strftime("%B"),
        year=last_month.strftime("%Y"),
        text=body_text,
        customer=customer,
        percent_online=stats.percent_online,
        out_of_sync_but_online=len(stats.out_of_date(datetime.now())),
    )


def get_html_other(body_text: str) -> str:
    """Return the email body's for non DDB customers."""

    template = MAIL_START + MAIL_END
    return template.format(text=body_text)


def get_recipients(customer: Customer) -> Iterator[str]:
    """Yield email addresses for the given customer."""

    for user_notification_email in UserNotificationEmail.select().where(
        UserNotificationEmail.customer == customer
    ):
        yield user_notification_email.email


def check_results_by_system(
    check_results: Iterable[CheckResults],
) -> dict[System, list[CheckResults]]:
    """Convert an iterable of check results into a dict of systems and its
    respective checks results.
    """

    result = defaultdict(list)

    for check_result in check_results:
        result[check_result.system].append(check_result)

    return result


def get_check_results_for_month(
    customer: Customer, month: date
) -> Iterable[CheckResults]:
    """Get the check results for the given customer and month."""

    return CheckResults.select(cascade=True).where(
        (Deployment.customer == customer)
        & (System.fitted == 1)
        & (CheckResults.timestamp >= month.replace(day=1))
        & (CheckResults.timestamp < first_day_of_next_month(month))
    )


def first_day_of_next_month(month: date) -> date:
    """Return the date of the first day of the next month."""

    return (month.replace(day=28) + timedelta(days=4)).replace(day=1)


def last_day_of_last_month(today: date) -> date:
    """Return the last day of the last month."""

    return today.replace(day=1) - timedelta(days=1)
