"""Monthly customer mailing."""

from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime, timedelta

from logging import basicConfig, getLogger

from typing import Iterator
from peewee import DoesNotExist


from hwdb import Deployment, System
from mdb import Customer

from his import ACCOUNT
from sysmon.mean_stats import MeanStats
from sysmon.orm import (
    CheckResults,
    UserNotificationEmail,
    ExtraUserNotificationEmail,
    Newsletter,
    Newsletterlistitems,
    StatisticUserNotificationEmail,
    Warningmail,
)
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from email.charset import Charset, QP
from functools import cache

from dataclasses import dataclass
from typing import Iterable, Optional
import requests

from sysmon.config import get_config
from locale import LC_TIME, setlocale
from emaillib import EMailsNotSent, Mailer, EMail

from PIL import Image
from io import BytesIO

from mdb import Address, Company, Customer
from hwdb import Deployment
from math import floor
from sysmon.functions import get_latest_check_results

__all__ = [
    "main",
    "send_mailing",
    "get_newsletter_by_date",
    "send_test_mails",
    "send_warning_test_mails",
]

LOGGER = getLogger("sysmon-mailing")
MAIL_BLOCK = """
<!DOCTYPE html>
<html lang="de">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Newsletter mieterinfo.tv</title>
	<style type="text/css">
		@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300..800&display=swap');

		body {{
			height: 100% !important;
			width: 100% !important;
		}}

		body, table, td, a {{
			-webkit-text-size-adjust: 100%;
			-ms-text-size-adjust: 100%;
		}}

		body, html {{
			margin: 0;
			padding: 0;
			width: 100% !important;
			background-color: #3f3f3f;
		}}

		a, a:hover, .link:hover {{
			text-decoration: none !important;
		}}

		a, h1, h2, h3, img, li, p, ul {{
			font-family: 'Open Sans', Helvetica, sans-serif;
			letter-spacing: 0;
		}}

		h1, h2, h3, h4, p {{
			padding: 0;
			margin: 0;
		}}

		h1, h2, h3, img, li, p, span, ul {{
			color: #000000;
		}}

		h1 {{
			font-size: 20px;
			font-weight: bold;
			line-height: 28px;
			margin: 0px auto 25px;
		}}

		h2 {{
			font-size: 18px;
			font-weight: bold;
			line-height: 25px;
			margin: 0px auto 15px;
		}}

		h3 {{
			font-size: 15px;
			font-weight: bold;
			line-height: 21px;
			margin: 0px auto 15px;
		}}

		img {{
			max-width: 700px;
			width: 100%;
			height: auto;
			border: 0;
			line-height: 100%;
			outline: none;
			text-decoration: none;
			display: block;
		}}

		p {{
			font-size: 13px;
			font-weight: normal;
			line-height: 20px;
			margin: 0px auto 15px;
		}}

		table {{
			border-collapse: collapse;
			mso-table-lspace: 0;
			mso-table-rspace: 0; 
		}}

		.btnGreen {{
			display: inline-block;
			color: #ffffff;
			font-size: 13px;
			line-height: 19px;
			text-decoration: none;
			background-color: #62a53a;
			border-radius: 18px;
			padding: 8px 15px;
			margin-top: 5px;
		}}

		.btnWhite {{
			display: inline-block;
			color: #000000;
			font-size: 13px;
			line-height: 19px;
			text-decoration: none;
			background-color: #ffffff;
			border-radius: 18px;
			padding: 8px 15px;
			margin-top: 5px;
		}}

		.container {{
			width: 100%;
			padding: 0;
		}}

		.content {{
			display: block;
			padding: 20px 20px 15px 20px;
		}}

		.contentWT1 {{
			display: block;
			padding: 20px;
		}}

		.contentWT2 {{
			display: block;
			padding: 0 20px 20px 20px;
		}}

		.contentWT2 table {{
			margin-top: 20px;
		}}

		.greenTable {{
			display: block;
			padding: 15px 20px 5px 20px;
			border-radius: 18px;
			background-color: #62a53a;
		}}

		.header {{
			padding: 10px 15px 20px 15px;
		}}

		.header img {{
			width: 40%;
			max-width: 228px;
		}}

		.small {{
			color: #ffffff;
			font-size: 12px;
			line-height: 17px;
			margin: 0;
		}}

		.whiteTable {{
			display: block;
			padding: 15px 20px 5px 20px;
			border-radius: 18px;
			background-color: #ffffff;
		}}

		@media only screen and (min-width: 700px) {{
			h1 {{
				font-size: 36px;
				line-height: 50px;
				margin: 0px auto 40px !important;
			}}

			h2 {{
				font-size: 24px;
				line-height: 34px;
				margin: 0px auto 25px !important;
			}}

			h3 {{
				font-size: 18px;
				line-height: 25px;
				margin: 0px auto 25px !important;
			}}

			.btnGreen {{
				font-size: 14px;
				line-height: 22px;
				text-decoration: none;
				border-radius: 22px;
				padding: 11px 22px;
			}}

			.btnWhite {{
				font-size: 14px;
				line-height: 22px;
				text-decoration: none;
				border-radius: 22px;
				padding: 11px 22px !important;
			}}

			.container {{
				max-width: 700px !important;
				margin: 0 auto !important;
				display: block !important;
			}}

			.content {{
				display: table-cell !important;
				padding: 45px 60px 30px 60px !important;
			}}

			.contentWT1 {{
				display: table-cell !important;	
				padding: 45px 60px 0 60px !important;
			}}

			.contentWT2 {{
				display: block;
				padding: 45px 60px !important;
			}}

			.contentWT2 table {{
				margin-top: 25px !important;
			}}

			.greenTable {{
				padding: 30px 30px 5px 30px !important;
				border-radius: 22px !important;
			}}

			.header {{
				padding: 20px 50px 40px 50px !important;
			}}

			.whiteTable {{
				padding: 30px 30px 5px 30px !important;
				border-radius: 22px !important;
			}}
		}}
	</style>
</head>

<body style="font-family: 'Open Sans', Helvetica, sans-serif">
	<div lang="de" dir="ltr" style="padding:20px; margin:0;">
		<table class="container" role="presentation" cellspacing="0" cellpadding="0" align="center" style="border-collapse:collapse;max-width:700px;width:100%;">
			<tr>
				<td class="header" style="width:100%;background-color:#2f3133;" align="right">
					<img width="228" height="90" src="cid:header" alt="mieterinfo.tv">
				</td>
			</tr>
			<tr>
				<td style="background-color:#ffffff;">
					<!--[if mso]>
					<table role="presentation" align="center" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
						<tr>
							<td>
					<![endif]-->
								<table align="center" role="presentation" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;max-width:700px;width:100%;">
									<tr>
										<td class="content" style="text-align: left;">
											<h1>{header}</h1>
											<p>{text}</p>
											{thelink}
										</td>
									</tr>
									<tr>
										<td align="center" width="700">{image}</td>
									</tr>
{ddbtext}
									<tr>
										<td class="contentWT2" style="text-align: left; background-color: #f5f5f5;">
											<h2>Updates aus dem letzten Monat</h2>
											{list}
										</td>
									</tr>
								</table>
					<!--[if mso]>
							</td>
						</tr>
					</table>
					<![endif]-->
				</td>
			</tr>
			<tr>
				<td class="footer" style="width:100%;background-color:#2f3133;">
					<!--[if mso]>
					<table role="presentation" align="center" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
						<tr>
							<td>
					<![endif]-->
								<table align="center" role="presentation" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;max-width:700px;width:100%;">
									<tr>
										<td class="content" style="text-align: left;">
											<!--[if mso]>
											<table role="presentation" align="center" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
												<tr>
													<td>
											<![endif]-->
														<table align="center" role="presentation" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;max-width:580;width:100%;margin-bottom: 25px;">
															<tr>
																<td colspan="2">
																	<p><a style="color: #ffffff; text-decoration: underline !important;" href="mailto:r.haupt@homeinfo.de?subject=UNSUBSCRIBE&body=Bitte tragen sie diese Emailadresse aus der Newsletter aus"><strong>Abbestellen</strong></a></p>
																</td>
															</tr>
															<tr>
																<td width="50%" valign="top" style="width: 50%;vertical-align: top;">
																	<p class="small">mieterinfo.tv<br>Kommunikationssysteme GmbH &amp; Co. KG<br>Burgstraße 6a<br>30823 Garbsen</p>
																</td>
																<td width="50%" valign="top" style="width: 50%;vertical-align: top;">
																	<p class="small">Fon: 0511 21 24 11 00<br><a style="color: #ffffff; text-decoration: none;" href="mailto:service@dasdigitalebrett.de">service@dasdigitalebrett.de</a><br><a style="color: #ffffff; text-decoration: none;" href="https://dasdigitalebrett.de" target="_blank">https://dasdigitalebrett.de</a></p>
																</td>
															</tr>
														</table>
											<!--[if mso]>
													</td>
												</tr>
											</table>
											<![endif]-->
										</td>
									</tr>
								</table>
					<!--[if mso]>
							</td>
						</tr>
					</table>
					<![endif]-->
				</td>
			</tr>
		</table>
	</div>
</body>
</html>
"""
LINK_BLOCK = """<p><a class="btnGreen" href="{mehrlink}" target="_blank"><strong>{merhlesen}</strong></a></p>"""
IMAGE_BLOCK = (
    """<img width="700" height="250" src="cid:image1" alt="Newsletter Bild">"""
)
DDB_TEXT = """<tr>
										<td class="contentWT1" style="text-align: left; background-color: #f5f5f5;">
											<!--[if mso]>
											<table role="presentation" align="center" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
												<tr>
													<td>
											<![endif]-->
														<table align="center" role="presentation" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;max-width:580;width:100%;">
															<tr>
																<td class="greenTable">
																	<h2>Ihre Statistik - {month} {year}</h2>
																	<p>Hiermit erhalten Sie einen Statusbericht für den Monat {month} {year} Ihrer Digitalen Bretter:<br>
<b>Im Monat {month} waren {percent_online}% Ihrer Digitalen Bretter online.</b><br>Sofern sich dazu im Vorfeld Fragen ergeben, stehen wir Ihnen natürlich wie gewohnt sehr gern zur Verfügung.<br>
Bitte nutzen Sie den Link zur detaillierten Monatsstatistik. Hier werden Ihnen auch weiterführende Abläufe beschrieben:<br>
<a class="btnWhite" href="https://portal.homeinfo.de/ddb-report?customer={customer.id}"" target="_blank" title="Link zur Webansicht"><strong>Link zur Webansicht</strong></a></p>
																</td>
															</tr>
														</table>
											<!--[if mso]>
													</td>
												</tr>
											</table>
											<![endif]-->
										</td>
									</tr>
"""
LIST_BLOCK = """<!--[if mso]>
											<table role="presentation" align="center" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
												<tr>
													<td>
											<![endif]-->
														<table align="center" role="presentation" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;max-width:580;width:100%;">
															<tr>
																<td class="whiteTable">
																	<h3>{header}</h3>
																	<p>{text}</p>
																</td>
															</tr>
														</table>
											<!--[if mso]>
													</td>
												</tr>
											</table>
											<![endif]-->
"""
FOOTER_TEXT = """ """


class MailImage:
    """Image as mail attachment"""

    src: str
    cid: str
    imagetype: str

    def __init__(self, src, cid, imagetype):
        self.cid = cid
        self.src = src
        self.imagetype = imagetype

    def __str__(self):
        return self.cid + self.src


@dataclass(unsafe_hash=True)
class AttachmentEMail(EMail):
    attachments: Optional[list] = None

    def to_mime_multipart(self) -> MIMEMultipart:
        """Returns a MIMEMultipart object for sending."""
        mime_multipart = MIMEMultipart("related")
        mime_multipart["Subject"] = self.subject
        mime_multipart["From"] = self.sender
        mime_multipart["To"] = self.recipient

        if self.reply_to is not None:
            mime_multipart["Reply-To"] = self.reply_to

        mime_multipart["Date"] = self.timestamp
        text_type = MIMEQPText if self.quoted_printable else MIMEText

        if self.html is not None:
            mime_multipart.attach(text_type(self.html, "html", self.charset))
        if self.plain is not None:
            mime_multipart.attach(text_type(self.plain, "plain", self.charset))

        for mailimage in self.attachments:
            if mailimage.src.startswith("http"):
                im = Image.open(requests.get(mailimage.src, stream=True).raw)
                byte_buffer = BytesIO()
                im.save(byte_buffer, im.format)
                image = MIMEImage(byte_buffer.getvalue())
                image.add_header("Content-ID", mailimage.cid)
                mime_multipart.attach(image)
            else:
                try:
                    fp = open(mailimage.src, "rb")
                    image = MIMEImage(fp.read())
                    fp.close()
                    image.add_header("Content-ID", mailimage.cid)
                    mime_multipart.attach(image)
                except Exception as error:
                    print("error image" + str(error))

        return mime_multipart


@cache
def get_qp_charset(charset: str) -> Charset:
    """Returns a quoted printable charset."""

    qp_charset = Charset(charset)
    qp_charset.body_encoding = QP
    return qp_charset


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
                newsletter.id,
                get_target_customers(),
                last_day_of_last_month(date.today()),
            )
        )
    )


class StatsSystemsByCustomer:
    customer: Customer
    systemsOnline: int()
    systemsOffline: int()
    systemsAll: int()

    def __init__(self, customer, systemsOnline=0, systemsOffline=0, systemsAll=0):
        self.customer = customer
        self.systemsOnline = systemsOnline
        self.systemsOffline = systemsOffline
        self.systemsAll = systemsAll

    @property
    def percentOffline(self):
        if self.systemsOffline == 0:
            return 0
        if self.systemsAll == 0:
            return 0
        return floor(self.systemsOffline / self.systemsAll * 100)


def create_warning_email(email, customer):
    # creates email with Customers who have more than minpercent offline systems

    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )
    mailbody = Warningmail.select().get().text
    mailsubject = Warningmail.select().get().subject
    minpercent = Warningmail.select().get().minpercent
    minsystems = Warningmail.select().get().minsystems
    stats = []
    stat = StatsSystemsByCustomer(customer)
    for checkresult in get_latest_check_results(
        (
            (Deployment.customer == customer)
            & (Deployment.testing == 0)
            & (System.testing == 0)
        )
    ):
        stat.systemsAll = stat.systemsAll + 1
        if checkresult.icmp_request:
            stat.systemsOnline = stat.systemsOnline + 1
        else:
            stat.systemsOffline = stat.systemsOffline + 1
        stats.append(stat)

    for stat in stats:
        try:
            customername = stat.customer.abbreviation
        except:
            customername = stat.customer
        if stat.percentOffline >= minpercent and stat.systemsAll >= minsystems:
            mailbody = mailbody.format(
                customer=customername,
                percentOffline=stat.percentOffline,
                systemsAll=stat.systemsAll,
                systemsOffline=stat.systemsOffline,
                customerId=stat.customer.id,
                weblink='<a href="https://portal.homeinfo.de/ddb-report?customer='
                + str(stat.customer.id)
                + '">Link zur Webansicht</a>',
            )
            mailsubject = mailsubject.format(
                customer=customername,
                percentOffline=stat.percentOffline,
                systemsAll=stat.systemsAll,
                systemsOffline=stat.systemsOffline,
            )
            return EMail(
                subject=mailsubject,
                sender=sender,
                recipient=email,
                html=mailbody,
            )


def create_statistic_email(email):
    # creates email with Customers who have more than 10% offline systems

    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )
    mailbody = """
    <style>
    td { 
    padding: 10px;
    padding-bottom:0px;
}

    </style>
    <p>Hier finden Sie eine Liste der Kunden, bei denen in den letzten 48 Stunden mehr als 10% ihrer Systeme offline waren
    </p> """
    stats = []
    for customer in Customer.select():
        stat = StatsSystemsByCustomer(customer)
        for checkresult in get_latest_check_results(
            (
                (Deployment.customer == customer)
                & (Deployment.testing == 0)
                & (System.testing == 0)
            )
        ):
            stat.systemsAll = stat.systemsAll + 1
            if checkresult.icmp_request:
                stat.systemsOnline = stat.systemsOnline + 1
            else:
                stat.systemsOffline = stat.systemsOffline + 1
        stats.append(stat)
    html = ""
    htmlSystemsHightlited = ""
    for stat in stats:
        try:
            customername = stat.customer.abbreviation
        except:
            customername = stat.customer
        if stat.percentOffline > 9:
            htmlSystemsHightlited = (
                htmlSystemsHightlited
                + "<tr><td>"
                + str(customername)
                + "</td>"
                + "<td>"
                + str(stat.percentOffline)
                + "% ("
                + str(stat.systemsOffline)
                + ")</td>"
                + "<td>"
                + str(stat.systemsAll)
                + "</td></tr>"
            )
        else:
            html = (
                html
                + "<tr><td>"
                + str(customername)
                + "</td>"
                + "<td>"
                + str(stat.percentOffline)
                + "% ("
                + str(stat.systemsOffline)
                + ")</td>"
                + "<td>"
                + str(stat.systemsAll)
                + "</td></tr>"
            )
    html = (
        "<h1>Alle Kunden</h1><table><tr><th>Kunde</th><th>Offline</th><th>Gesamt</th></tr>"
        + html
        + "</table>"
    )
    htmlSystemsHightlited = (
        "<table><tr><th>Kunde</th><th>Offline</th><th>Gesamt</th></tr>"
        + htmlSystemsHightlited
        + "</table>"
    )

    return EMail(
        subject="Homeinfo Service Notification",
        sender=sender,
        recipient=email,
        html=mailbody + htmlSystemsHightlited + html,
    )


def send_statistic_test_mails():
    # send statistic mail to user logged into sysmon
    get_mailer().send([create_statistic_email(ACCOUNT.email)])


def send_warning_test_mails():
    # send warning mails to user logged into sysmon
    get_mailer().send(get_warning_mails_test())


def get_warning_mails_test():
    for email in UserNotificationEmail.select():
        message = create_warning_email(ACCOUNT.email, email.customer)
        if message != None:
            yield message


def send_warning_mails():
    # send warning mails to user logged into sysmon

    get_mailer().send(get_warning_mails())


def get_warning_mails():
    for email in UserNotificationEmail.select():
        message = create_warning_email(email.email, email.customer)
        if message != None:
            yield message


def statistic():
    # sends statistic mailing to users in database
    get_mailer().send(create_statistic_emails())


def send_test_mails(newsletter: int):
    get_mailer().send(
        [create_customer_test_email(newsletter, ACCOUNT.customer, ACCOUNT.email)]
    )
    get_mailer().send([create_other_test_email(newsletter, ACCOUNT.email)])


def create_other_test_emails(newsletter: int):
    for email in ExtraUserNotificationEmail.select():
        yield create_other_test_email(newsletter, email.email)


def create_statistic_emails():
    for email in StatisticUserNotificationEmail.select():
        yield create_statistic_email(email.email)


def create_other_test_email(newsletter: int, recipient: str):
    """Creates a Mail for non DDB clients"""
    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )
    nl_to_send = get_newsletter_by_date(
        Newsletter.select().where(Newsletter.id == newsletter).get().period
    )
    html = get_html_other(nl_to_send)
    images_cid = list()
    images_cid.append(
        MailImage(
            "https://sysmon.homeinfo.de/newsletter-image/1137174", "header", "PNG"
        )
    )
    try:
        image_to_attach = nl_to_send.image.id
        images_cid.append(
            MailImage(
                "https://sysmon.homeinfo.de/newsletter-image/" + str(image_to_attach),
                "image1",
                "JPEG",
            )
        )
    except:
        pass

    return AttachmentEMail(
        subject=nl_to_send.subject,
        sender=sender,
        recipient=recipient,
        html=html,
        attachments=images_cid,
    )


def create_customer_test_email(newsletter: int, customer: Customer, recipient: str):
    nl_to_send = get_newsletter_by_date(
        Newsletter.select().where(Newsletter.id == newsletter).get().period
    )
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
        html = get_html(
            nl_to_send,
            customer,
            "0",
            last_month,
        )

    else:
        html = get_html(
            nl_to_send,
            customer,
            MeanStats.from_system_check_results(check_results).percent_online,
            last_month,
        )
    images_cid = list()
    images_cid.append(
        MailImage(
            "https://sysmon.homeinfo.de/newsletter-image/1137174", "header", "PNG"
        )
    )
    try:
        image_to_attach = nl_to_send.image.id
        images_cid.append(
            MailImage(
                "https://sysmon.homeinfo.de/newsletter-image/" + str(image_to_attach),
                "image1",
                "JPEG",
            )
        )
    except:
        pass
    return AttachmentEMail(
        subject=nl_to_send.subject,
        sender=sender,
        recipient=recipient,
        html=html,
        attachments=images_cid,
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
    newsletter, customers: Iterable[Customer], last_month: date
) -> Iterator[EMail]:
    """Create monthly notification emails for the given customers."""

    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )

    for customer in customers:
        yield from create_customer_emails(
            newsletter, customer, sender=sender, last_month=last_month
        )


def create_customer_emails(
    newsletter, customer: Customer, sender: str, last_month: date
) -> Iterator[EMail]:
    """Create the system status summary emails for the given month."""
    nl_to_send = get_newsletter_by_date(
        Newsletter.select().where(Newsletter.id == newsletter).get().period
    )

    if not (
        check_results := check_results_by_system(
            get_check_results_for_month(customer, last_month)
        )
    ):
        html = get_html(
            nl_to_send,
            customer,
            "0",
            last_month,
        )

    else:
        html = get_html(
            nl_to_send,
            customer,
            MeanStats.from_system_check_results(check_results).percent_online,
            last_month,
        )
    images_cid = list()
    images_cid.append(
        MailImage(
            "https://sysmon.homeinfo.de/newsletter-image/1137174", "header", "PNG"
        )
    )
    try:
        image_to_attach = nl_to_send.image.id
        images_cid.append(
            MailImage(
                "https://sysmon.homeinfo.de/newsletter-image/" + str(image_to_attach),
                "image1",
                "JPEG",
            )
        )
    except:
        pass

    for recipient in get_recipients(customer):
        yield AttachmentEMail(
            subject=nl_to_send.subject,
            sender=sender,
            recipient=recipient,
            html=html,
            attachments=images_cid,
        )


def get_html(
    nl_to_send: Newsletter, customer: Customer, stats, last_month: date
) -> str:
    """Return the email body's for DDB customers."""
    if nl_to_send.image:
        image = IMAGE_BLOCK
    else:
        image = ""
    setlocale(LC_TIME, "de_DE.UTF-8")
    template = MAIL_BLOCK
    if nl_to_send.more_text:
        linktemplate = LINK_BLOCK
        linktemplate = linktemplate.format(
            merhlesen=nl_to_send.more_text,
            mehrlink=nl_to_send.more_link,
        )
    else:
        linktemplate = ""

    listelements = ""
    for li in Newsletterlistitems.select().where(
        Newsletterlistitems.newsletter == nl_to_send.id
    ):
        litemplate = LIST_BLOCK
        listelements = listelements + litemplate.format(header=li.header, text=li.text)
    ddb_text = DDB_TEXT.format(
        month=last_month.strftime("%B"),
        year=last_month.strftime("%Y"),
        customer=customer,
        percent_online=stats,
        out_of_sync_but_online=len(stats.out_of_date(datetime.now())),
    )
    return template.format(
        ddbtext=ddb_text,
        text=nl_to_send.text,
        thelink=linktemplate,
        header=nl_to_send.header,
        list=listelements,
        image=image,
    )


def get_html_other(nl_to_send: Newsletter) -> str:
    """Return the email body's for non DDB customers."""

    template = MAIL_BLOCK
    if nl_to_send.image:
        image = IMAGE_BLOCK
    else:
        image = ""

    if nl_to_send.more_text:
        linktemplate = LINK_BLOCK
        linktemplate = linktemplate.format(
            merhlesen=nl_to_send.more_text,
            mehrlink=nl_to_send.more_link,
        )
    else:
        linktemplate = ""
    listelements = ""
    for li in Newsletterlistitems.select().where(
        Newsletterlistitems.newsletter == nl_to_send.id
    ):
        litemplate = LIST_BLOCK
        listelements = listelements + litemplate.format(header=li.header, text=li.text)

    return template.format(
        text=nl_to_send.text,
        thelink=linktemplate,
        header=nl_to_send.header,
        list=listelements,
        image=image,
        ddbtext="",
    )


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
