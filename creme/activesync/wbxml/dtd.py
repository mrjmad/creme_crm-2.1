# -*- coding: utf-8 -*-

################################################################################
#    This file is a modified version of dtd.py from SynCE project
#    Original file located at http://synce.svn.sourceforge.net/viewvc/synce/trunk/sync-engine/SyncEngine/wbxml/dtd.py
################################################################################

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
# 
#    Copyright (c) 2006 Ole André Vadla Ravnås <oleavr@gmail.com>
#    Copyright (c) 2007 Dr J A Gow <J.A.Gow@furrybubble.co.uk>
#    Copyright (C) 2009-2011  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

###############################################################################
# DTD.py
#
# WBXML document type description for Airsync. The reverse mapping is
# generated at initialization time and the actual DTD fed to the codecs is
# a tuple of the (forward,reverse) mappings. Only the forward mapping need
# be explicitly listed
#
###############################################################################


#Inspired by SyncEngine Dtd

AirsyncDTD_Forward = {
    'codes' : {
        0 : {
            0x05 : 'Sync',
            0x06 : 'Responses',
            0x07 : 'Add',
            0x08 : 'Change',
            0x09 : 'Delete',
            0x0a : 'Fetch',
            0x0b : 'SyncKey',
            0x0c : 'ClientId',
            0x0d : 'ServerId',
            0x0e : 'Status',
            0x0f : 'Collection',
            0x10 : 'Class',
            0x11 : 'Version',
            0x12 : 'CollectionId',
            0x13 : 'GetChanges',
            0x14 : 'MoreAvailable',
            0x15 : 'WindowSize',
            0x16 : 'Commands',
            0x17 : 'Options',
            0x18 : 'FilterType',
            0x19 : 'Truncation',
            0x1a : 'RtfTruncation',
            0x1b : 'Conflict',
            0x1c : 'Collections',
            0x1d : 'ApplicationData',
            0x1e : 'DeletesAsMoves',
            0x1f : 'NotifyGUID',
            0x20 : 'Supported',
            0x21 : 'SoftDelete',
            0x22 : 'MIMESupport',
            0x23 : 'MIMETruncation',
        }, 1 : {
            0x05 : 'Anniversary',
            0x06 : 'AssistantName',
            0x07 : 'AssistnamePhoneNumber',
            0x08 : 'Birthday',
            0x09 : 'Body',
            0x0a : 'BodySize',
            0x0b : 'BodyTruncated',
            0x0c : 'Business2PhoneNumber',
            0x0d : 'BusinessCity',
            0x0e : 'BusinessCountry',
            0x0f : 'BusinessPostalCode',
            0x10 : 'BusinessState',
            0x11 : 'BusinessStreet',
            0x12 : 'BusinessFaxNumber',
            0x13 : 'BusinessPhoneNumber',
            0x14 : 'CarPhoneNumber',
            0x15 : 'Categories',
            0x16 : 'Category',
            0x17 : 'Children',
            0x18 : 'Child',
            0x19 : 'CompanyName',
            0x1a : 'Department',
            0x1b : 'Email1Address',
            0x1c : 'Email2Address',
            0x1d : 'Email3Address',
            0x1e : 'FileAs',
            0x1f : 'FirstName',
            0x20 : 'Home2PhoneNumber',
            0x21 : 'HomeCity',
            0x22 : 'HomeCountry',
            0x23 : 'HomePostalCode',
            0x24 : 'HomeState',
            0x25 : 'HomeStreet',
            0x26 : 'HomeFaxNumber',
            0x27 : 'HomePhoneNumber',
            0x28 : 'JobTitle',
            0x29 : 'LastName',
            0x2a : 'MiddleName',
            0x2b : 'MobilePhoneNumber',
            0x2c : 'OfficeLocation',
            0x2d : 'OtherCity',
            0x2e : 'OtherCountry',
            0x2f : 'OtherPostalCode',
            0x30 : 'OtherState',
            0x31 : 'OtherStreet',
            0x32 : 'PagerNumber',
            0x33 : 'RadioPhoneNumber',
            0x34 : 'Spouse',
            0x35 : 'Suffix',
            0x36 : 'Title',
            0x37 : 'WebPage',
            0x38 : 'YomiCompanyName',
            0x39 : 'YomiFirstName',
            0x3a : 'YomiLastName',
            0x3b : 'Rtf',
            0x3c : 'Picture',
        }, 2 : {
            0x05 : 'Attachment',
            0x06 : 'Attachments',
            0x07 : 'AttName',
            0x08 : 'AttSize',
            0x09 : 'AttOid',
            0x0a : 'AttMethod',
            0x0b : 'AttRemoved',
            0x0c : 'Body',
            0x0d : 'BodySize',
            0x0e : 'BodyTruncated',
            0x0f : 'DateReceived', 
            0x10 : 'DisplayName',
            0x11 : 'DisplayTo',
            0x12 : 'Importance',
            0x13 : 'MessageClass',
            0x14 : 'Subject',
            0x15 : 'Read',
            0x16 : 'To',
            0x17 : 'Cc',
            0x18 : 'From',
            0x19 : 'Reply-To',
            0x1a : 'AllDayEvent',
            0x1b : 'Categories',
            0x1c : 'Category',
            0x1d : 'DtStamp',
            0x1e : 'EndTime',
            0x1f : 'InstanceType',
            0x20 : 'BusyStatus',
            0x21 : 'Location',
            0x22 : 'MeetingRequest',
            0x23 : 'Organizer',
            0x24 : 'RecurrenceId',
            0x25 : 'Reminder',
            0x26 : 'ResponseRequested',
            0x27 : 'Recurrences',
            0x28 : 'Recurrence',
            0x29 : 'Type',
            0x2a : 'Until',
            0x2b : 'Occurrences',
            0x2c : 'Interval',
            0x2d : 'DayOfWeek',
            0x2e : 'DayOfMonth',
            0x2f : 'WeekOfMonth',
            0x30 : 'MonthOfYear',
            0x31 : 'StartTime',
            0x32 : 'Sensitivity',
            0x33 : 'TimeZone',
            0x34 : 'GlobalObjId',
            0x35 : 'ThreadTopic',
            0x36 : 'MIMEData',
            0x37 : 'MIMETruncated',
            0x38 : 'MIMESize',
            0x39 : 'InternetCPID',
        }, 3 : {
            0x05 : 'Notify',
            0x06 : 'Notification',
            0x07 : 'Version',
            0x08 : 'Lifetime',
            0x09 : 'DeviceInfo',
            0x0a : 'Enable',
            0x0b : 'Folder',
            0x0c : 'ServerId',
            0x0d : 'DeviceAddress',
            0x0e : 'ValidCarrierProfiles',
            0x0f : 'CarrierProfile',
            0x10 : 'Status',
            0x11 : 'Responses',
#            0x05 : 'Version='1.1'',
            0x12 : 'Devices',
            0x13 : 'Device',
            0x14 : 'Id',
            0x15 : 'Expiry',
            0x16 : 'NotifyGUID',
        }, 4 : {
            0x05 : 'Timezone',
            0x06 : 'AllDayEvent',
            0x07 : 'Attendees',
            0x08 : 'Attendee',
            0x09 : 'Email',
            0x0a : 'Name',
            0x0b : 'Body',
            0x0c : 'BodyTruncated',
            0x0d : 'BusyStatus',
            0x0e : 'Categories',
            0x0f : 'Category',
            0x10 : 'Rtf',
            0x11 : 'DtStamp',
            0x12 : 'EndTime',
            0x13 : 'Exception',
            0x14 : 'Exceptions',
            0x15 : 'Deleted',
            0x16 : 'ExceptionStartTime',
            0x17 : 'Location',
            0x18 : 'MeetingStatus',
            0x19 : 'OrganizerEmail',
            0x1a : 'OrganizerName',
            0x1b : 'Recurrence',
            0x1c : 'Type',
            0x1d : 'Until',
            0x1e : 'Occurrences',
            0x1f : 'Interval',
            0x20 : 'DayOfWeek',
            0x21 : 'DayOfMonth',
            0x22 : 'WeekOfMonth',
            0x23 : 'MonthOfYear',
            0x24 : 'Reminder',
            0x25 : 'Sensitivity',
            0x26 : 'Subject',
            0x27 : 'StartTime',
            0x28 : 'UID',
        }, 5 : {
            0x05 : 'Moves',
            0x06 : 'Move',
            0x07 : 'SrcMsgId',
            0x08 : 'SrcFldId',
            0x09 : 'DstFldId',
            0x0a : 'Response',
            0x0b : 'Status',
            0x0c : 'DstMsgId',
        }, 6 : {
            0x05 : 'GetItemEstimate',
            0x06 : 'Version',
            0x07 : 'Collections',
            0x08 : 'Collection',
            0x09 : 'Class',
            0x0a : 'CollectionId',
            0x0b : 'DateTime',
            0x0c : 'Estimate',
            0x0d : 'Response',
            0x0e : 'Status',
        }, 7 : {
            0x05 : 'Folders',
            0x06 : 'Folder',
            0x07 : 'DisplayName',
            0x08 : 'ServerId',
            0x09 : 'ParentId',
            0x0a : 'Type',
            0x0b : 'Response',
            0x0c : 'Status',
            0x0d : 'ContentClass',
            0x0e : 'Changes',
            0x0f : 'Add',
            0x10 : 'Delete',
            0x11 : 'Update',
            0x12 : 'SyncKey',
            0x13 : 'FolderCreate',
            0x14 : 'FolderDelete',
            0x15 : 'FolderUpdate',
            0x16 : 'FolderSync',
            0x17 : 'Count',
            0x18 : 'Version',
        }, 8 : {
            0x05 : 'CalendarId',
            0x06 : 'CollectionId',
            0x07 : 'MeetingResponse',
            0x08 : 'RequestId',
            0x09 : 'Request',
            0x0a : 'Result',
            0x0b : 'Status',
            0x0c : 'UserResponse',
            0x0d : 'Version',
        }, 9 : {
            0x05 : 'Body',
            0x06 : 'BodySize',
            0x07 : 'BodyTruncated',
            0x08 : 'Categories',
            0x09 : 'Category',
            0x0a : 'Complete',
            0x0b : 'DateCompleted',
            0x0c : 'DueDate',
            0x0d : 'UtcDueDate',
            0x0e : 'Importance',
            0x0f : 'Recurrence',
            0x10 : 'Type',
            0x11 : 'Start',
            0x12 : 'Until',
            0x13 : 'Occurrences',
            0x14 : 'Interval',
            0x16 : 'DayOfWeek',
            0x15 : 'DayOfMonth',
            0x17 : 'WeekOfMonth',
            0x18 : 'MonthOfYear',
            0x19 : 'Regenerate',
            0x1a : 'DeadOccur',
            0x1b : 'ReminderSet',
            0x1c : 'ReminderTime',
            0x1d : 'Sensitivity',
            0x1e : 'StartDate',
            0x1f : 'UtcStartDate',
            0x20 : 'Subject',
            0x21 : 'Rtf',
        }, 0xa : {
            0x05 : 'ResolveRecipients',
            0x06 : 'Response',
            0x07 : 'Status',
            0x08 : 'Type',
            0x09 : 'Recipient',
            0x0a : 'DisplayName',
            0x0b : 'EmailAddress',
            0x0c : 'Certificates',
            0x0d : 'Certificate',
            0x0e : 'MiniCertificate',
            0x0f : 'Options',
            0x10 : 'To',
            0x11 : 'CertificateRetrieval',
            0x12 : 'RecipientCount',
            0x13 : 'MaxCertificates',
            0x14 : 'MaxAmbiguousRecipients',
            0x15 : 'CertificateCount',
        }, 0xb : {
            0x05 : 'ValidateCert',
            0x06 : 'Certificates',
            0x07 : 'Certificate',
            0x08 : 'CertificateChain',
            0x09 : 'CheckCRL',
            0x0a : 'Status',
        }, 0xc : {
            0x05 : 'CustomerId',
            0x06 : 'GovernmentId',
            0x07 : 'IMAddress',
            0x08 : 'IMAddress2',
            0x09 : 'IMAddress3',
            0x0a : 'ManagerName',
            0x0b : 'CompanyMainPhone',
            0x0c : 'AccountName',
            0x0d : 'NickName',
            0x0e : 'MMS',
        }, 0xd : {
            0x05 : 'Ping',
            0x07 : 'PingStatus',
            0x08 : 'HeartbeatInterval',
            0x09 : 'PingFolders',
            0x0a : 'PingFolderId',
            0x0b : 'Id',
            0x0c : 'Class',
        }, 0xe : {
#            0x05 : "Provision",
#            0x06 : "Policies",
#            0x07 : "Policy",
#            0x08 : "PolicyType",
#            0x09 : "PolicyKey",
#            0x0A : "Data",
#            0x0B : "Status",
#            0x0C : "RemoteWipe",
#            0x0D : "EASProvisionDoc",
            0x05 : "Provision",
            0x06 : "Policies",
            0x07 : "Policy",
            0x08 : "PolicyType",
            0x09 : "PolicyKey",
            0x0A : "Data",
            0x0B : "Status",
            0x0C : "RemoteWipe",
            0x0D : "EASProvisionDoc",
            0x0E : "DevicePasswordEnabled",
            0x0F : "AlphanumericDevicePasswordRequired",
            0x10 : "DeviceEncryptionEnabled",
#            0x10 : "RequireStorageCardEncryption"(equivalent : "DeviceEncryptionEnabled"),
            0x11 : "PasswordRecoveryEnabled",
            0x13 : "AttachmentsEnabled",
            0x14 : "MinDevicePasswordLength",
            0x15 : "MaxInactivityTimeDeviceLock",
            0x16 : "MaxDevicePasswordFailedAttempts",
            0x17 : "MaxAttachmentSize",
            0x18 : "AllowSimpleDevicePassword",
            0x19 : "DevicePasswordExpiration",
            0x1A : "DevicePasswordHistory",
            0x1B : "AllowStorageCard",
            0x1C : "AllowCamera",
            0x1D : "RequireDeviceEncryption",
            0x1E : "AllowUnsignedApplications",
            0x1F : "AllowUnsignedInstallationPackages",
            0x20 : "MinDevicePasswordComplexCharacters",
            0x21 : "AllowWiFi",
            0x22 : "AllowTextMessaging",
            0x23 : "AllowPOPIMAPEmail",
            0x24 : "AllowBluetooth",
            0x25 : "AllowIrDA",
            0x26 : "RequireManualSyncWhenRoaming",
            0x27 : "AllowDesktopSync",
            0x28 : "MaxCalendarAgeFilter",
            0x29 : "AllowHTMLEmail",
            0x2A : "MaxEmailAgeFilter",
            0x2B : "MaxEmailBodyTruncationSize",
            0x2C : "MaxEmailHTMLBodyTruncationSize",
            0x2D : "RequireSignedSMIMEMessages",
            0x2E : "RequireEncryptedSMIMEMessages",
            0x2F : "RequireSignedSMIMEAlgorithm",
            0x30 : "RequireEncryptionSMIMEAlgorithm",
            0x31 : "AllowSMIMEEncryptionAlgorithmNegotiation",
            0x32 : "AllowSMIMESoftCerts",
            0x33 : "AllowBrowser",
            0x34 : "AllowConsumerEmail",
            0x35 : "AllowRemoteDesktop",
            0x36 : "AllowInternetSharing",
            0x37 : "UnapprovedInROMApplicationList",
            0x38 : "ApplicationName",
            0x39 : "ApprovedApplicationList",
            0x3A : "Hash",
        }, 0xf : {

        }, 0x10: {

        }, 0x11: {
            0x05 : "BodyPreference",
            0x06 : "Type",
            0x07 : "TruncationSize",
            0x08 : "AllOrNone",
            0x0A : "Body",
            0x0B : "Data",
            0x0C : "EstimatedDataSize",
            0x0D : "Truncated",
            0x0E : "Attachments",
            0x0F : "Attachment",
            0x10 : "DisplayName",
            0x11 : "FileReference",
            0x12 : "Method",
            0x13 : "ContentId",
            0x14 : "ContentLocation",
            0x15 : "IsInline",
            0x16 : "NativeBodyType",
            0x17 : "ContentType",
            0x18 : "Preview",
            0x19 : "BodyPartPreference",
            0x1A : "BodyPart",
            0x1B : "Status",
        }, 0x12: {
            0x05 : "Settings",
            0x06 : "Status",
            0x07 : "Get",
            0x08 : "Set",
            0x09 : "Oof",
            0x0A : "OofState",
            0x0B : "StartTime",
            0x0C : "EndTime",
            0x0D : "OofMessage",
            0x0E : "AppliesToInternal",
            0x0F : "AppliesToExternalKnown",
            0x10 : "AppliesToExternalUnknown",
            0x11 : "Enabled",
            0x12 : "ReplyMessage",
            0x13 : "BodyType",
            0x14 : "DevicePassword",
            0x15 : "Password",
            0x16 : "DeviceInformation",
            0x17 : "Model",
            0x18 : "IMEI",
            0x19 : "FriendlyName",
            0x1A : "OS",
            0x1B : "OSLanguage",
            0x1C : "PhoneNumber",
            0x1D : "UserInformation",
            0x1E : "EmailAddresses",
            0x1F : "SmtpAddress",
            0x20 : "UserAgent",
            0x21 : "EnableOutboundSMS",
            0x22 : "MobileOperator",
            0x23 : "PrimarySmtpAddress",
            0x24 : "Accounts",
            0x25 : "Account",
            0x26 : "AccountId",
            0x27 : "AccountName",
            0x28 : "UserDisplayName",
            0x29 : "SendDisabled",
            0x2B : "ihsManagementInformation",
        }, 0x13: {

        }, 0x14: {

        }, 0x15: {

        }, 0x16: {

        }, 0x17: {

        },
    }, 'namespaces' : {
    	0 : 'AirSync:',
        1 : 'Contacts:',
        2 : 'Email:',
        3 : 'AirNotify:',#Seems deprecated
        4 : 'Calendar:',
        5 : 'Move:',
        6 : 'GetItemEstimate:',
        7 : 'FolderHierarchy:',
        8 : 'MeetingResponse:',
        9 : 'Tasks:',
        0xA : 'ResolveRecipients:',
        0xB : 'ValidateCert:',
        0xC : 'Contacts2:',
        0xD : 'Ping:',
        0xE : 'Provision:',
        0xF : 'Search:',#TODO
        0x10: 'Gal:',#TODO
        0x11: 'AirSyncBase:',#TODO: To be tested
        0x12: 'Settings:',
        0x13: 'DocumentLibrary:',#TODO
        0x14: 'ItemOperations:',#TODO
        0x15: 'ComposeMail:',#TODO
        0x16: 'Email2:',#TODO
        0x17: 'Notes:',#TODO
    }
}

AirsyncDTD_Reverse = {'namespaces': {}, 'codes': {}}
AirsyncDTD = []

###############################################################################
# InitializeDTD
#
# Populate and initialize

def InitializeDTD():
    reverse_namespaces = AirsyncDTD_Reverse['namespaces']
    for (nsid, nsname) in AirsyncDTD_Forward['namespaces'].items():
        reverse_namespaces[nsname] = nsid

    reverse_codes = AirsyncDTD_Reverse['codes']
    forward_codes = AirsyncDTD_Forward['codes']
    for (cp, value) in forward_codes.items():
        reverse_codes[cp] = {}
        for (tagid, tagname) in forward_codes[cp].items():
            reverse_codes[cp][tagname] = tagid

    AirsyncDTD.append(AirsyncDTD_Forward)
    AirsyncDTD.append(AirsyncDTD_Reverse)
