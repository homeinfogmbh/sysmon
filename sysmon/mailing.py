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

__all__ = ["main", "send_mailing", "get_newsletter_by_date", "send_test_mails"]


IMAGE_BLOCK = """
  <div class="hide414">
    <img class="hide414" src="cid:image1" style="-ms-interpolation-mode: bicubic; clear: both; display: block; height: auto; max-width: 700px; outline: none; text-decoration: none; width: 100%;" alt="" width="700" height="" border="0">
  </div>
"""

LIST_BLOCK = """
<tr >

     <td class="p2b" style="width: 32px; color: #000000; font-family: Helvetica, Arial, sans-serif; font-size: 20px;line-height: 26px;
 font-weight: 700;  padding-bottom: 0px; padding-left:12px; padding-top: 7px;" valign="top">
     <p>•</p>

      </td>


     <td style="direction:ltr;text-align:left; padding-bottom: 7px; padding-top: 7px; padding-right: 12px;" valign="top">


        <table class="basetable" style="table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">

        <tbody><tr>
          <td class="p1b" style="color: #000000; font-family: Helvetica, Arial, sans-serif; font-size: 20px; font-weight: 700; line-height: 26px; padding-bottom: 7px; padding-top: 0px;">{header}</td>
        </tr>

        <tr>
          <td class="p2" style="color: #000000; font-family: Helvetica, Arial, sans-serif; font-size: 16px; font-weight: normal; line-height: 22px; padding-bottom: 7px; padding-top: 0px;"><p>{text}</p>
</td>
        </tr>

        </tbody></table>  


     </td>
  </tr>
  """

LINK_BLOCK = """
<tr>
                     <td style="direction:ltr;text-align:left;">
<!--[if (gte mso 9)|(IE)]>
<table width="250" align="left" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<![endif]-->
   <div class="btn" style="font-family: Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 700; line-height: 22px;" lang="x-btn"> <a href="{mehrlink}"  style="background-color: #000000; border-color: #000000; border-radius: 0px; border-style: solid; border-width: 13px 18px; color: #ffffff; display: inline-block; letter-spacing: 1px; max-width: 300px; min-width: 100px; text-align: center; text-decoration: none; transition: all 0.2s ease-in;"><span style="float:left;text-align:left;">{merhlesen}</span> 
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
"""


MAIL_START = """<html>
<style>h1,.h1{{
  font-size: 60px !important;
  line-height: 66px !important;
}}h2,.h2{{
  font-size: 44px !important;
  line-height: 50px !important;
}}.btn a:hover{{
  background-color:#000000!important; 
  border-color:#000000!important;
}}.textcta a:hover{{
  color:#000000!important;
  }}p {{margin: 0 !important;}}.divbox:hover, * [lang~="x-divbox"]:hover {{
  background-color: #000000 !important;
}}.boxfont:hover, * [lang~="x-boxfont"]:hover {{
  color: #ffffff !important;
  
}}
.bgcol{{
background-color: #ABE366;
}}
a {{text-decoration: none;}}a[x-apple-data-detectors] {{ color: inherit !important; text-decoration: none !important; font-size: inherit !important; font-family: inherit !important; font-weight: inherit !important; line-height: inherit !important }}table{{ mso-table-lspace: 0; mso-table-rspace: 0; mso-table-lspace: 0; border: none; border-collapse: collapse; border-spacing: 0;}}p {{margin: 0 !important;}}h1, .h1, .h1l {{ font-size: 60px !important; line-height: 66px !important; }}h2, .h2 {{ font-size: 44px !important; line-height: 50px !important; }}ul, ol {{margin:0; margin-left:8px !important;}}u + .body ul, u + .body ol {{ margin-left: 8px !important; }}.show670, .show414 {{display:none;}}sup {{ line-height:0; font-size:70%; }}</style>

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
						    <img class="hide414" src="cid:header">
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
        <table class="t11of12 layout" style="border-collapse: collapse;  width: 100%;" cellspacing="0" cellpadding="0" border="0" align="left">
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
<table align="left" cellpadding="0" cellspacing="0" border="0">
  <tr>
     <td>
        <![endif]-->
        <table class="t9of12 layout" style="border-collapse: collapse; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="left">
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
        <table class="t6of12 layout" style="border-collapse: collapse; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="left">
           <tbody><tr>
              <td style="direction:ltr;text-align:left;font-size: 1px; height: 1px; line-height: 1px; padding-left: 0px !important; padding-right: 0px !important;">
                 <table style="border-collapse: collapse; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
                    <tbody>


                      <tr>
                       <td class="p1" style="direction:ltr;text-align:left;color: #000000; font-family: Helvetica, Arial, sans-serif; font-size: 20px; font-weight: normal; line-height: 26px; padding-bottom: 7px; padding-top: 7px;"><div>{text}
"""

MAIL_END = """</div>
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
                    {thelink}
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


{image}







             </td>
           </tr>
        </tbody></table>
     </td>
  </tr>
</tbody></table>
<table style="border:0;border-collapse:collapse;border-spacing:0;margin:auto;max-width:700px;mso-table-lspace:0;mso-table-rspace:0" class="tron" width="100%" cellspacing="0" cellpadding="0" border="0">
<tbody>
<tr>
<td align="center">
<table style="background-color:#fff;border:0;border-collapse:collapse;border-spacing:0;margin:auto;mso-table-lspace:0;mso-table-rspace:0" class="basetable" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#ffffff">
<tbody>
<tr>
<td align="center">
<!--[if (gte mso 9)|(IE)]>
<table width="700" align="center" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="center">
<![endif]-->
<table class="basetable" style="border:0;border-collapse:collapse;border-spacing:0;mso-table-lspace:0;mso-table-rspace:0" width="100%" cellspacing="0" cellpadding="0" border="0">
<tbody>
<tr>
<td style="background-color:#ffffff" align="center">
<table class="basetable" style="border:0;border-collapse:collapse;border-spacing:0;mso-table-lspace:0;mso-table-rspace:0" width="100%" cellspacing="0" cellpadding="0" border="0">
<tbody>
<tr>
<td>
<!--[if (gte mso 9)|(IE)]>
<table width="100%" align="center" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<![endif]-->
<table class="basetable" style="border:0;border-collapse:collapse;border-spacing:0;mso-table-lspace:0;mso-table-rspace:0" width="100%" cellspacing="0" cellpadding="0" border="0">
<tbody>
<tr>
<td>
<!--[if (gte mso 9)|(IE)]>
<table width="100%" align="center" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<![endif]-->
<table style="border:0;border-collapse:collapse;border-spacing:0;mso-table-lspace:0;mso-table-rspace:0" class="" width="100%" cellspacing="0" cellpadding="0" border="0">
<tbody>
<tr>
<td>

<table style="border-collapse: collapse; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0">
<tbody>

<tr>
<td style="font-size:0; line-height: 1px; " height="25">&nbsp;
</td>
</tr>

<tr>
<td class="outsidegutter" style="direction:ltr;text-align:left; ; padding:15px 14px 15px 14px;" align="left">
<table style="border-collapse: collapse; width: 100%;" cellspacing="0" cellpadding="0" border="0">
<tbody><tr>
<td style="direction:ltr;text-align:left;">
<!--[if (gte mso 9)|(IE)]>
<table width="560" align="center" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<![endif]-->
<table class="t10of12" style="Margin: 0 auto; border-collapse: collapse; max-width: 560px; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="center">
<tbody><tr>
<td style="direction:ltr;text-align:left;">
<table style="border-collapse: collapse; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
<tbody>


<tr>
<td style="direction:ltr;text-align:left;">
<table style="border-collapse: collapse; table-layout: fixed; width: 560px;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
<tbody>

{list}

</tbody></table>
</td>
</tr>


<tr><td colspan=2 style="color: #000000; font-family: Helvetica, Arial, sans-serif; font-size: 16px; font-weight: normal; line-height: 22px; padding-bottom: 7px; padding-top: 0px">

{ddbtext}
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

<tr>
<td style="font-size:0; line-height: 1px; " height="25">&nbsp;
</td>
</tr>

</tbody></table>
</td>
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
<!--[if (gte mso 9)|(IE)]>
</td>
</tr>
</table>
<![endif]-->
</td>
</tr>
</tbody>
</table>
</td>
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
<!-- END LIST-->
</td>
</tr>
<!-- END BODY-->
</tbody>
</table>
<table style="background-color: #000000; width: 100%;"  width="100%" cellspacing="0" cellpadding="0" border="0">
<tbody><tr>
<td class="outsidegutter" style="direction:ltr;text-align:left;" align="left">
<table style="width: 100%;" class="" cellspacing="0" cellpadding="0" border="0">



<tbody><tr>
<td style="direction:ltr;text-align:left;padding: 30px 14px 30px 14px;">
<!--[if (gte mso 9)|(IE)]>
<table width="560" align="center" cellpadding="0" cellspacing="0" border="0">
<tr>
<td>
<![endif]-->
<table class="t10of12" style="Margin: 0 auto; max-width: 560px; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="center">
<tbody><tr>
<td>
<table style="direction: rtl; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
<tbody><tr>
<td class="ignoreTd" style="font-size:0; text-align: left;">
<table class="t6of12" style="direction: ltr; display: inline-block; max-width: 560px; vertical-align: top; width: 100%;" cellspacing="0" cellpadding="0" border="0">
<tbody><tr>
<td>
<table style="table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
<tbody><tr>
<td>
<!--[if (gte mso 9)|(IE)]>
<table width="468" align="left" cellpadding="0" cellspacing="0" border="0">
<tr>
<td width="168">
<![endif]-->
<table class="t3of12" style="max-width: 168px; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="left">
<tbody><tr>
<td style="direction:ltr;text-align:left;padding: 0 12px;">
<table style="table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">

<tbody>




<tr>
<td class="white" style="color: rgb(0, 0, 0); font-family: Helvetica, Arial, sans-serif; font-size: 12px; line-height: 18px; padding: 3px 0px; direction: ltr; text-align: left;">

<a href="mailto:r.haupt@homeinfo.de?subject=UNSUBSCRIBE&body=Bitte tragen sie diese Emailadresse aus der Newsletter aus" style="text-decoration: none; color: #ffffff;">Abbestellen</a>

</td>
</tr>


</tbody></table>
</td>
</tr>
</tbody></table>
<!--[if (gte mso 9)|(IE)]>
</td>
<td width="300" valign="top" style="vertical-align: top;">
<![endif]-->

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
</tr>
</tbody></table>
<!--[if (gte mso 9)|(IE)]>
</td>
</tr>
</table>
<![endif]-->
</td>
</tr>
<!-- END top half -->
<!-- bottom half -->
<tr>
<td style="direction:ltr;text-align:left; padding: 0px 14px 30px 14px;">
<!--[if (gte mso 9)|(IE)]>
<table width="560" align="center" cellpadding="0" cellspacing="0" border="0">
<tr>
<td width="560">
<![endif]-->
<table class="t10of12" style="Margin: 0 auto; max-width: 560px; width: 100%;" cellspacing="0" cellpadding="0" border="0" align="center">
<tbody><tr>
<td>
<table style="direction: rtl; table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
<tbody><tr>
<td style="font-size:0; text-align: left">
<!--[if (gte mso 9)|(IE)]>
<table width="560" align="left" cellpadding="0" cellspacing="0" border="0">
<tr>
<td width="224">
<![endif]-->
<table class="t4of12" style="direction: ltr; display: inline-block; max-width: 224px; vertical-align: top; width: 100%;" cellspacing="0" cellpadding="0" border="0">
<tbody><tr>
<td style="direction:ltr;text-align:left;padding: 0 12px;">
<table style="table-layout: fixed;" cellspacing="0" cellpadding="0" border="0" align="left">
<tbody><tr>
<td style="padding-bottom: 12px; direction:ltr;text-align:left;">

 
</td>
</tr>
</tbody></table>
</td>
</tr>
</tbody></table>
<!--[if (gte mso 9)|(IE)]>
</td>
<td width="336">
<![endif]-->
<table class="t6of12" style="direction: ltr; display: inline-block; max-width: 336px; vertical-align: top; width: 100%;" cellspacing="0" cellpadding="0" border="0">
<tbody><tr>
<td style="direction:ltr;text-align:left;padding: 0 12px;">
<table style="table-layout: fixed; width: 100%;" width="100%" cellspacing="0" cellpadding="0" border="0" align="left">
<tbody><tr>
<td style="direction:ltr;text-align:left;color: #e5e5e5; font-family: Helvetica, Arial, sans-serif; font-size: 10px; line-height: 18px;">






mieterinfo.tv<br>
Kommunikationssysteme GmbH & Co. KG<br><br>

Burgstraße 6a<br>
30826 Garbsen<br>

Fon.: 0511 21 24 11 00<br>

service@dasdigitalebrett.de<br>
<a href="https://dasdigitalebrett.de/ "  style="text-decoration: none; color: #e5e5e5">https://dasdigitalebrett.de/ </a>




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

</td>
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

</html>"""

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
                im.save(byte_buffer, mailimage.imagetype)
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


def create_statistic_email(email):
    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )
    mailbody = """<p>Hier finden Sie eine Liste der Kunden, bei denen in den letzten 48 Stunden mehr als 10% ihrer Systeme offline waren
    </p> """
    stats = []
    for customer in Customer.select():
        stat = StatsSystemsByCustomer(customer.id)
        for checkresult in get_latest_check_results(
            ((Deployment.customer == customer) & (Deployment.testing == 0))
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
    get_mailer().send([create_statistic_email(ACCOUNT.email)])


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
    nl_to_send = get_newsletter_by_date(
        Newsletter.select().where(Newsletter.id == newsletter).get().period
    )
    html = get_html_other(nl_to_send)
    images_cid = list()
    images_cid.append(
        MailImage(
            "https://sysmon.homeinfo.de/newsletter-image/1074324", "header", "PNG"
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
        html = get_html_other(nl_to_send)

    else:
        html = get_html(
            nl_to_send,
            customer,
            MeanStats.from_system_check_results(check_results),
            last_month,
        )
    images_cid = list()
    images_cid.append(
        MailImage(
            "https://sysmon.homeinfo.de/newsletter-image/1074324", "header", "PNG"
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
        html = get_html_other(nl_to_send)

    else:
        html = get_html(
            nl_to_send,
            customer,
            MeanStats.from_system_check_results(check_results),
            last_month,
        )
    images_cid = list()
    images_cid.append(
        MailImage(
            "https://sysmon.homeinfo.de/newsletter-image/1074324", "header", "PNG"
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
    nl_to_send: Newsletter, customer: Customer, stats: MeanStats, last_month: date
) -> str:
    """Return the email body's for DDB customers."""
    if nl_to_send.image:
        image = IMAGE_BLOCK
    else:
        image = ""

    template = MAIL_START + MAIL_END
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
        percent_online=stats.percent_online,
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

    template = MAIL_START + MAIL_END
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
