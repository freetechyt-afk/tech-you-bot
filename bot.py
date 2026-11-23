// ==============================================================================
// TECH YOU - ENTERPRISE LICENSE & 3-TIER ACCOUNTANT ENGINE (v10.7.2)
// Creator: Sumit Arora (TECH YOU)
//
// TABS IN GOOGLE SHEET:
// 1. "Keys"        -> Master DRM & Key Registry
// 2. "YT_Members"  -> Official YouTube Studio Members List (Imported via CSV)
// 3. "Dashboard"   -> Real-time Tier & Growth Analytics
//
// 3 TIERS MAINTAINED:
// - ⚡ Tech You Legends ⚡
// - ⚡ Titans ⚡
// - ⚡ Supporters ⚡
// ==============================================================================

const SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1KPjyDT0vZkozW72Do2uE6687uU_FCZp-6qrQDxdSpdE/edit";
const BOT_API_SECRET = "TECH_YOU_BOT_SECRET_2026";
const MOD_DOWNLOAD_URL = "https://drive.google.com/file/d/13c2oYCD25p21DBFO3_dIW2r4ZfTM_0AI/view?usp=sharing";
const DISCORD_INVITE_URL = "https://discord.gg/FrjUgCmRNG";
const TIMEZONE = "Asia/Kolkata";

function getSpreadsheet() {
  try {
    var ss = SpreadsheetApp.openByUrl(SPREADSHEET_URL);
    if (ss) return ss;
  } catch (err) {
    try {
      var ssActive = SpreadsheetApp.getActiveSpreadsheet();
      if (ssActive) return ssActive;
    } catch (e2) {}
  }
  throw new Error("Google Sheet nahi khul pa rahi hai.");
}

function getKeysSheet() {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName("Keys");
  
  if (!sheet) {
    // If "Keys" doesn't exist, check if "Sheet1" exists
    let sheet1 = ss.getSheetByName("Sheet1");
    if (sheet1) {
      sheet1.setName("Keys");
      sheet = sheet1;
    } else {
      sheet = ss.insertSheet("Keys");
      sheet.appendRow(["License_Key", "Status", "Member_Name", "Member_Tier", "Channel_ID", "Bound_HWID", "Created_Date", "Activated_Date", "Expiry_Date"]);
      formatKeysHeader(sheet);
    }
  }

  // AUTO-MIGRATE: If a tab named "Sheet1" still exists alongside "Keys", migrate any old keys from "Sheet1" into "Keys"
  const sheet1 = ss.getSheetByName("Sheet1");
  if (sheet1 && sheet1.getSheetId() !== sheet.getSheetId()) {
    const s1Data = sheet1.getDataRange().getValues();
    const keysData = sheet.getDataRange().getValues();
    const existingKeysSet = new Set();
    for (let i = 1; i < keysData.length; i++) {
      existingKeysSet.add(String(keysData[i][0]).trim().toUpperCase());
    }

    for (let r = 1; r < s1Data.length; r++) {
      const s1Key = String(s1Data[r][0] || "").trim().toUpperCase();
      if (s1Key.startsWith("TY-") && !existingKeysSet.has(s1Key)) {
        // Old Sheet1 format: [Key, Status, Bound_HWID, YouTube_Name, Member_Email, Created_Date, Activated_Date, Expiry_Date]
        const s1Status = String(s1Data[r][1] || "ACTIVE").trim().toUpperCase();
        const s1Hwid = String(s1Data[r][2] || "").trim();
        const s1Name = String(s1Data[r][3] || "").trim();
        const s1Email = String(s1Data[r][4] || "").trim();
        const s1Created = String(s1Data[r][5] || "").trim();
        const s1Activated = String(s1Data[r][6] || "").trim();
        const s1Expiry = String(s1Data[r][7] || "").trim();

        // New format: [License_Key, Status, Member_Name, Member_Tier, Channel_ID, Bound_HWID, Created_Date, Activated_Date, Expiry_Date]
        sheet.appendRow([s1Key, s1Status, s1Name, "⚡ Supporters ⚡", s1Email, s1Hwid, s1Created, s1Activated, s1Expiry]);
        existingKeysSet.add(s1Key);
      }
    }
  }

  return sheet;
}

function getYtMembersSheet() {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName("YT_Members");
  if (!sheet) {
    sheet = ss.insertSheet("YT_Members");
    sheet.appendRow(["Member_Name", "Channel_ID", "Channel_URL", "Member_Tier", "Status_Type", "Months_Active", "Last_Updated"]);
    formatYtMembersHeader(sheet);
  }
  return sheet;
}

function getDashboardSheet() {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName("Dashboard");
  if (!sheet) {
    sheet = ss.insertSheet("Dashboard");
  }
  return sheet;
}

function generateUniqueKey(sheet) {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let key = "";
  let exists = true;
  
  while (exists) {
    let p1 = "";
    let p2 = "";
    for (let i = 0; i < 4; i++) p1 += chars.charAt(Math.floor(Math.random() * chars.length));
    for (let i = 0; i < 4; i++) p2 += chars.charAt(Math.floor(Math.random() * chars.length));
    key = "TY-" + p1 + "-" + p2;
    
    const data = sheet.getRange("A:A").getValues();
    exists = data.some(row => row[0] === key);
  }
  return key;
}

// Extract clean Channel ID (UC...) from any string or URL
function extractChannelId(inputStr) {
  if (!inputStr) return "";
  inputStr = String(inputStr).trim();
  const match = inputStr.match(/UC[a-zA-Z0-9_-]{22}/);
  if (match) return match[0];
  return inputStr;
}

// ------------------------------------------------------------------------------
// HTTP GET DISPATCHER
// ------------------------------------------------------------------------------
function doGet(e) {
  try {
    const params = e ? e.parameter : {};
    const action = params.action || "";

    // 1. GTA 5 IN-GAME MOD ACTIVATION / VALIDATION
    if (action === "activate" || action === "check" || (params.key && params.hwid)) {
      return handleGameCheck(params.key, params.hwid);
    }

    // 2. DISCORD BOT: KEY GENERATE / RE-CHECK / RENEW (3-Tier Supported)
    if (action === "generate_key") {
      if (params.secret !== BOT_API_SECRET) {
        return ContentService.createTextOutput(JSON.stringify({ status: "UNAUTHORIZED" })).setMimeType(ContentService.MimeType.JSON);
      }
      return handleBotGenerateKey(params);
    }

    // 3. DISCORD BOT: REVOKE KEY
    if (action === "revoke_key") {
      if (params.secret !== BOT_API_SECRET) {
        return ContentService.createTextOutput(JSON.stringify({ status: "UNAUTHORIZED" })).setMimeType(ContentService.MimeType.JSON);
      }
      return handleBotRevokeKey(params);
    }

    // 4. DISCORD BOT: GET 3-TIER STATS & DASHBOARD
    if (action === "get_stats") {
      if (params.secret !== BOT_API_SECRET) {
        return ContentService.createTextOutput(JSON.stringify({ status: "UNAUTHORIZED" })).setMimeType(ContentService.MimeType.JSON);
      }
      return ContentService.createTextOutput(JSON.stringify(getLiveStats())).setMimeType(ContentService.MimeType.JSON);
    }

    // 5. DIAGNOSTICS: INSPECT TABS & KEYS
    if (action === "diag") {
      if (params.secret !== BOT_API_SECRET) {
        return ContentService.createTextOutput(JSON.stringify({ status: "UNAUTHORIZED" })).setMimeType(ContentService.MimeType.JSON);
      }
      const ss = getSpreadsheet();
      const allSheets = ss.getSheets();
      const report = {};
      allSheets.forEach(s => {
        report[s.getName()] = s.getDataRange().getValues().slice(0, 10);
      });
      return ContentService.createTextOutput(JSON.stringify(report)).setMimeType(ContentService.MimeType.JSON);
    }

    // 5. DEFAULT: OFFICIAL MEMBER PORTAL
    return HtmlService.createHtmlOutput(getHtmlPage())
      .setTitle("TECH YOU - VIP Member Portal (v10.7.2)")
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "ERROR", message: err.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}

// ------------------------------------------------------------------------------
// HTTP POST DISPATCHER (For uploading CSV member lists from Discord Bot)
// ------------------------------------------------------------------------------
function doPost(e) {
  try {
    const postData = JSON.parse(e.postData.contents || "{}");
    const action = postData.action || "";
    
    if (postData.secret !== BOT_API_SECRET) {
      return ContentService.createTextOutput(JSON.stringify({ status: "UNAUTHORIZED" })).setMimeType(ContentService.MimeType.JSON);
    }

    // ACCOUNTANT ACTION: SYNC MEMBERS CSV
    if (action === "sync_csv") {
      const result = syncMembersCsvData(postData.members || []);
      return ContentService.createTextOutput(JSON.stringify(result)).setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({ status: "UNKNOWN_ACTION" })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "ERROR", message: err.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}

// ------------------------------------------------------------------------------
// ACCOUNTANT LOGIC: SYNC CSV, UPDATE TIERS, & PURGE CANCELLED MEMBERS
// ------------------------------------------------------------------------------
function syncMembersCsvData(membersList) {
  if (!Array.isArray(membersList) || membersList.length === 0) {
    return { status: "EMPTY_DATA", message: "No members found in CSV." };
  }

  const ytSheet = getYtMembersSheet();
  const keysSheet = getKeysSheet();
  const now = new Date();
  const updateTimestamp = Utilities.formatDate(now, TIMEZONE, "dd-MMM-yyyy HH:mm");

  // 1. Clear existing YT_Members data (except header row 1)
  const lastRow = ytSheet.getLastRow();
  if (lastRow > 1) {
    ytSheet.getRange(2, 1, lastRow - 1, 7).clearContent();
  }

  const activeChannelIds = new Set();
  const activeMembersMap = {};
  const rowsToAppend = [];

  let countLegends = 0;
  let countTitans = 0;
  let countSupporters = 0;
  let countJoined = 0;
  let countRejoined = 0;

  for (let i = 0; i < membersList.length; i++) {
    const m = membersList[i];
    const name = String(m.name || "").trim();
    const profileUrl = String(m.profile_url || "").trim();
    const channelId = extractChannelId(profileUrl || m.channel_id || "");
    const tier = String(m.tier || "⚡ Supporters ⚡").trim();
    const statusType = String(m.status_type || "Joined").trim();
    const months = String(m.months || "1").trim();

    if (channelId) {
      activeChannelIds.add(channelId);
      activeMembersMap[channelId] = { name: name, tier: tier };
    }

    // Tier counts
    const tierLower = tier.toLowerCase();
    if (tierLower.includes("legend")) countLegends++;
    else if (tierLower.includes("titan")) countTitans++;
    else countSupporters++;

    // Growth counts
    if (statusType.toLowerCase().includes("re-join")) countRejoined++;
    else countJoined++;

    rowsToAppend.push([name, channelId, profileUrl, tier, statusType, months, updateTimestamp]);
  }

  // Batch insert into YT_Members sheet
  if (rowsToAppend.length > 0) {
    ytSheet.getRange(2, 1, rowsToAppend.length, 7).setValues(rowsToAppend);
  }

  // 2. AUDIT & RECONCILE KEYS SHEET (DEACTIVATE CANCELLED MEMBERS)
  const keysData = keysSheet.getDataRange().getValues();
  let countRevoked = 0;
  let countMaintained = 0;

  for (let k = 1; k < keysData.length; k++) {
    const rowStatus = String(keysData[k][1] || "").trim().toUpperCase();
    const rowChannelId = extractChannelId(keysData[k][4] || keysData[k][3] || "");

    if (rowChannelId && (rowStatus === "ACTIVE" || rowStatus === "")) {
      // Check if this channel is still an active member in the new CSV
      if (!activeChannelIds.has(rowChannelId)) {
        // CANCELLED MEMBER DETECTED -> REVOKE!
        keysSheet.getRange(k + 1, 2).setValue("REVOKED (MEMBERSHIP ENDED)");
        countRevoked++;
      } else {
        // UPDATE TIER IF CHANGED
        const currentTier = activeMembersMap[rowChannelId].tier;
        keysSheet.getRange(k + 1, 4).setValue(currentTier); // Col D: Member_Tier
        countMaintained++;
      }
    }
  }

  SpreadsheetApp.flush();

  // 3. REFRESH DASHBOARD TAB
  updateDashboardAnalytics(countLegends, countTitans, countSupporters, countJoined, countRejoined, countMaintained, countRevoked);

  return {
    status: "SUCCESS",
    totalMembers: membersList.length,
    tierLegends: countLegends,
    tierTitans: countTitans,
    tierSupporters: countSupporters,
    newJoined: countJoined,
    reJoined: countRejoined,
    keysMaintained: countMaintained,
    keysRevoked: countRevoked,
    timestamp: updateTimestamp
  };
}

// ------------------------------------------------------------------------------
// LIVE DASHBOARD ANALYTICS WRITER
// ------------------------------------------------------------------------------
function updateDashboardAnalytics(legends, titans, supporters, joined, rejoined, activeKeys, revoked) {
  const dashSheet = getDashboardSheet();
  dashSheet.clear();

  const totalMembers = legends + titans + supporters;
  const nowStr = Utilities.formatDate(new Date(), TIMEZONE, "dd-MMM-yyyy HH:mm");

  const dashData = [
    ["👑 TECH YOU GAMING - VIP MEMBERSHIP & TIER DASHBOARD", "", ""],
    ["Last Synchronized:", nowStr, ""],
    ["", "", ""],
    ["📊 MEMBERSHIP SUMMARY", "COUNT", "STATUS"],
    ["Total Active Members", totalMembers, "100% Verified"],
    ["🟢 Fresh Joined This Month", joined, "New Growth"],
    ["🔄 Re-joined (Renewals)", rejoined, "Loyal Members"],
    ["", "", ""],
    ["🏆 3-TIER BREAKDOWN", "MEMBERS", "ACCESS LEVEL"],
    ["⚡ Tech You Legends ⚡", legends, "Highest VIP Tier"],
    ["⚡ Titans ⚡", titans, "Executive Tier"],
    ["⚡ Supporters ⚡", supporters, "Community Member Tier"],
    ["", "", ""],
    ["🔒 IN-GAME DRM STATUS", "COUNT", "NOTES"],
    ["Active In-Game Keys", activeKeys, "Single-PC HWID Bound"],
    ["Revoked / Cancelled", revoked, "Deactivated Automatically"]
  ];

  dashSheet.getRange(1, 1, dashData.length, 3).setValues(dashData);

  // Formatting Dashboard
  dashSheet.getRange("A1:C1").setBackground("#0d1527").setFontColor("#00e5ff").setFontWeight("bold").setFontSize(14);
  dashSheet.getRange("A4:C4").setBackground("#16203a").setFontColor("#00ff88").setFontWeight("bold");
  dashSheet.getRange("A9:C9").setBackground("#16203a").setFontColor("#ffb830").setFontWeight("bold");
  dashSheet.getRange("A14:C14").setBackground("#16203a").setFontColor("#ff0055").setFontWeight("bold");
  
  dashSheet.autoResizeColumn(1);
  dashSheet.autoResizeColumn(2);
  dashSheet.autoResizeColumn(3);
}

// ------------------------------------------------------------------------------
// GET LIVE STATS FOR DISCORD BOT
// ------------------------------------------------------------------------------
function getLiveStats() {
  const ytSheet = getYtMembersSheet();
  const keysSheet = getKeysSheet();
  const ytData = ytSheet.getDataRange().getValues();
  const keysData = keysSheet.getDataRange().getValues();

  let legends = 0, titans = 0, supporters = 0, joined = 0, rejoined = 0;

  for (let i = 1; i < ytData.length; i++) {
    const tier = String(ytData[i][3] || "").toLowerCase();
    const type = String(ytData[i][4] || "").toLowerCase();
    if (tier.includes("legend")) legends++;
    else if (tier.includes("titan")) titans++;
    else supporters++;

    if (type.includes("re-join")) rejoined++;
    else joined++;
  }

  let inGameActive = 0, inGameRevoked = 0;
  for (let k = 1; k < keysData.length; k++) {
    const st = String(keysData[k][1] || "").toUpperCase();
    if (st === "ACTIVE") inGameActive++;
    else if (st.includes("REVOKED")) inGameRevoked++;
  }

  return {
    totalMembers: (legends + titans + supporters),
    tierLegends: legends,
    tierTitans: titans,
    tierSupporters: supporters,
    newJoined: joined,
    reJoined: rejoined,
    inGameActive: inGameActive,
    inGameRevoked: inGameRevoked
  };
}

// ------------------------------------------------------------------------------
// DISCORD BOT: KEY GENERATE / RE-CHECK / RENEW
// ------------------------------------------------------------------------------
function handleBotGenerateKey(params) {
  const discordId = String(params.discord_id || "").trim();
  const discordName = String(params.discord_name || "").trim();
  const channelInput = String(params.channel_input || "").trim();
  const cleanChannelId = extractChannelId(channelInput);

  const ytSheet = getYtMembersSheet();
  const keysSheet = getKeysSheet();
  const ytData = ytSheet.getDataRange().getValues();
  const keysData = keysSheet.getDataRange().getValues();
  const now = new Date();

  // Step 1: Find member in YT_Members sheet (By Channel ID, URL, or Name)
  let foundMember = null;
  if (ytData.length > 1) {
    for (let i = 1; i < ytData.length; i++) {
      const rowName = String(ytData[i][0] || "").trim().toLowerCase();
      const rowChannelId = String(ytData[i][1] || "").trim();
      
      if ((cleanChannelId && rowChannelId === cleanChannelId) || 
          (channelInput && (rowName === channelInput.toLowerCase() || rowName.includes(channelInput.toLowerCase())))) {
        foundMember = {
          name: ytData[i][0],
          channelId: ytData[i][1],
          tier: ytData[i][3]
        };
        break;
      }
    }
  }

  // Fallback if YT_Members is still initializing or admin generated
  const memberName = foundMember ? foundMember.name : discordName;
  const memberTier = foundMember ? foundMember.tier : "⚡ Supporters ⚡";
  const finalChannelId = foundMember ? foundMember.channelId : (cleanChannelId || discordId);

  // Step 2: Strict 1 Member = 1 Key Check
  for (let k = 1; k < keysData.length; k++) {
    const rowStatus = String(keysData[k][1] || "").trim().toUpperCase();
    const existingKey = keysData[k][0];
    const expiryDateStr = keysData[k][8] || keysData[k][7];

    const col2 = String(keysData[k][2] || "").trim().toLowerCase(); // Member_Name or HWID
    const col3 = String(keysData[k][3] || "").trim().toLowerCase(); // Member_Tier or YouTube_Name
    const col4 = String(keysData[k][4] || "").trim();               // Channel_ID or Email
    const col5 = String(keysData[k][5] || "").trim();               // Bound_HWID

    // Check matches by Channel ID, Discord ID, or Name:
    const isChannelMatch = cleanChannelId && (col4 === cleanChannelId || col3.includes(cleanChannelId) || col2.includes(cleanChannelId));
    const isDiscordMatch = discordId && (col4.includes(discordId) || col3.includes(discordId) || col2.includes(discordId));
    const isNameMatch = memberName && (
      col2 === memberName.toLowerCase() || 
      col3 === memberName.toLowerCase() ||
      col3.includes(memberName.toLowerCase()) ||
      col2.includes(memberName.toLowerCase())
    );

    if (isChannelMatch || isDiscordMatch || isNameMatch) {
      // Keep Channel ID and Tier updated in sheet
      if (cleanChannelId && keysData[k][4] !== cleanChannelId) {
        keysSheet.getRange(k + 1, 5).setValue(cleanChannelId);
      }
      if (memberTier && keysData[k][3] !== memberTier) {
        keysSheet.getRange(k + 1, 4).setValue(memberTier);
      }
      if (memberName && !keysData[k][2]) {
        keysSheet.getRange(k + 1, 3).setValue(memberName);
      }
      SpreadsheetApp.flush();

      // If already active or unused, return existing key
      if (rowStatus === "ACTIVE" || rowStatus === "" || rowStatus === "UNUSED") {
        return ContentService.createTextOutput(JSON.stringify({
          status: "ALREADY_HAS_KEY",
          key: existingKey,
          tier: memberTier,
          downloadUrl: MOD_DOWNLOAD_URL,
          expiryDate: expiryDateStr ? String(expiryDateStr) : "30 Days from activation"
        })).setMimeType(ContentService.MimeType.JSON);
      }

      // If EXPIRED or REVOKED -> SMART RENEW (+30 Days)
      const newExpObj = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000));
      const newExpDate = Utilities.formatDate(newExpObj, TIMEZONE, "dd-MMM-yyyy HH:mm");
      const renewDate = Utilities.formatDate(now, TIMEZONE, "dd-MMM-yyyy HH:mm");

      keysSheet.getRange(k + 1, 2).setValue("ACTIVE");
      keysSheet.getRange(k + 1, 4).setValue(memberTier);
      keysSheet.getRange(k + 1, 8).setValue(renewDate);
      keysSheet.getRange(k + 1, 9).setValue(newExpDate);
      SpreadsheetApp.flush();

      return ContentService.createTextOutput(JSON.stringify({
        status: "RENEWED_KEY",
        key: existingKey,
        tier: memberTier,
        downloadUrl: MOD_DOWNLOAD_URL,
        expiryDate: newExpDate
      })).setMimeType(ContentService.MimeType.JSON);
    }
  }

  // Step 3: Issue New Key
  const newKey = generateUniqueKey(keysSheet);
  const createdDate = Utilities.formatDate(now, TIMEZONE, "dd-MMM-yyyy HH:mm");

  // Columns: [License_Key, Status, Member_Name, Member_Tier, Channel_ID, Bound_HWID, Created_Date, Activated_Date, Expiry_Date]
  keysSheet.appendRow([newKey, "ACTIVE", memberName, memberTier, finalChannelId, "", createdDate, "", ""]);
  SpreadsheetApp.flush();

  return ContentService.createTextOutput(JSON.stringify({
    status: "SUCCESS",
    key: newKey,
    tier: memberTier,
    downloadUrl: MOD_DOWNLOAD_URL
  })).setMimeType(ContentService.MimeType.JSON);
}

// ------------------------------------------------------------------------------
// DISCORD BOT: REVOKE KEY
// ------------------------------------------------------------------------------
function handleBotRevokeKey(params) {
  const discordId = String(params.discord_id || "").trim();
  const keysSheet = getKeysSheet();
  const data = keysSheet.getDataRange().getValues();
  let count = 0;

  for (let i = 1; i < data.length; i++) {
    const sourceStr = String(data[i][4] || data[i][3] || "").trim();
    if (sourceStr.includes(discordId)) {
      keysSheet.getRange(i + 1, 2).setValue("REVOKED (LEFT SERVER)");
      count++;
    }
  }
  return ContentService.createTextOutput(JSON.stringify({ status: "SUCCESS", revoked: count })).setMimeType(ContentService.MimeType.JSON);
}

// ------------------------------------------------------------------------------
// GTA 5 IN-GAME MOD ACTIVATION (HWID LOCK & 30-DAY COUNTDOWN)
// ------------------------------------------------------------------------------
function handleGameCheck(key, hwid) {
  key = (key || "").trim().toUpperCase();
  hwid = (hwid || "").trim();
  if (!key) return ContentService.createTextOutput(JSON.stringify({ status: "INVALID_KEY", message: "No key provided" })).setMimeType(ContentService.MimeType.JSON);

  const sheet = getKeysSheet();
  const data = sheet.getDataRange().getValues();
  let rowIndex = -1;
  let rowData = null;

  for (let i = 1; i < data.length; i++) {
    if (String(data[i][0]).trim().toUpperCase() === key) {
      rowIndex = i + 1;
      rowData = data[i];
      break;
    }
  }

  if (rowIndex === -1) {
    return ContentService.createTextOutput(JSON.stringify({ status: "INVALID_KEY", message: "Key not found" })).setMimeType(ContentService.MimeType.JSON);
  }

  let status = String(rowData[1] || "").trim().toUpperCase(); // Col B: Status
  let sheetHwid = String(rowData[5] || rowData[2] || "").trim(); // Col F (New Format) OR Col C (Old Format)
  let expiryDate = rowData[8] || rowData[7];                     // Col I (New Format) OR Col H (Old Format)

  if (status.includes("REVOKED") || status === "BLOCKED" || status === "BANNED") {
    return ContentService.createTextOutput(JSON.stringify({ status: "REVOKED", message: "License revoked" })).setMimeType(ContentService.MimeType.JSON);
  }

  const now = new Date();

  // 1. FIRST TIME IN-GAME ACTIVATION -> LOCK HWID!
  if (!sheetHwid || sheetHwid === "") {
    const actDate = Utilities.formatDate(now, TIMEZONE, "dd-MMM-yyyy HH:mm");
    const expObj = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000)); // 30 Days
    const expDate = Utilities.formatDate(expObj, TIMEZONE, "dd-MMM-yyyy HH:mm");

    sheet.getRange(rowIndex, 6).setValue(hwid);     // Col F: Bound_HWID
    sheet.getRange(rowIndex, 2).setValue("ACTIVE");   // Col B: Status
    sheet.getRange(rowIndex, 8).setValue(actDate);  // Col H: Activated_Date
    sheet.getRange(rowIndex, 9).setValue(expDate);  // Col I: Expiry_Date
    SpreadsheetApp.flush();

    return ContentService.createTextOutput(JSON.stringify({
      status: "SUCCESS",
      message: "Key successfully activated for 30 days",
      daysRemaining: 30,
      expiryDate: expObj.toISOString().split("T")[0]
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // 2. HWID MISMATCH (Key shared on a different PC)
  if (sheetHwid !== hwid) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "HWID_MISMATCH",
      message: "Key is already bound to another PC! (1 Key = 1 PC Only)"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // 3. EXPIRY CHECK
  if (expiryDate) {
    const expDateObj = new Date(expiryDate);
    const diffTime = expDateObj.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays <= 0) {
      sheet.getRange(rowIndex, 2).setValue("EXPIRED");
      return ContentService.createTextOutput(JSON.stringify({
        status: "EXPIRED",
        message: "License expired. Please renew."
      })).setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "SUCCESS",
      message: "License valid",
      daysRemaining: diffDays,
      expiryDate: expDateObj.toISOString().split("T")[0]
    })).setMimeType(ContentService.MimeType.JSON);
  }

  return ContentService.createTextOutput(JSON.stringify({
    status: "SUCCESS",
    message: "License valid",
    daysRemaining: 30
  })).setMimeType(ContentService.MimeType.JSON);
}

// ------------------------------------------------------------------------------
// HEADERS FORMATTING HELPERS
// ------------------------------------------------------------------------------
function formatKeysHeader(sheet) {
  const headerRange = sheet.getRange(1, 1, 1, 9);
  headerRange.setBackground("#0d1527").setFontColor("#00e5ff").setFontWeight("bold").setFontSize(11).setHorizontalAlignment("center");
}

function formatYtMembersHeader(sheet) {
  const headerRange = sheet.getRange(1, 1, 1, 7);
  headerRange.setBackground("#141829").setFontColor("#ffb830").setFontWeight("bold").setFontSize(11).setHorizontalAlignment("center");
}

// ------------------------------------------------------------------------------
// HTML PORTAL (ANTI-PIRACY & DISCORD GATEWAY)
// ------------------------------------------------------------------------------
function getHtmlPage() {
  return `
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TECH YOU - VIP Member Portal (v10.7.2)</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
    <style>
      * { box-sizing: border-box; margin: 0; padding: 0; }
      body {
        background: radial-gradient(circle at top, #141829 0%, #090a10 100%);
        color: #ffffff;
        font-family: 'Montserrat', sans-serif;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
      }
      .card {
        background: rgba(22, 27, 46, 0.95);
        backdrop-filter: blur(16px);
        max-width: 520px;
        width: 100%;
        padding: 40px 32px;
        border-radius: 20px;
        box-shadow: 0 16px 50px rgba(0, 0, 0, 0.8);
        border: 1px solid rgba(0, 229, 255, 0.25);
        text-align: center;
      }
      .shield-icon { font-size: 48px; margin-bottom: 12px; display: inline-block; filter: drop-shadow(0 0 12px rgba(0, 229, 255, 0.6)); }
      .brand-title { font-size: 26px; font-weight: 800; letter-spacing: 1.5px; background: linear-gradient(135deg, #00e5ff 0%, #0077ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 6px; }
      .subtitle { color: #8c93a8; font-size: 14px; font-weight: 600; margin-bottom: 25px; }
      .badge { display: inline-block; background: rgba(0, 229, 255, 0.12); color: #00e5ff; border: 1px solid rgba(0, 229, 255, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 20px; }
      .tiers-box { display: flex; justify-content: center; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
      .tier-pill { font-size: 11px; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
      .tier-legend { background: rgba(255, 0, 85, 0.2); color: #ff0055; border: 1px solid #ff0055; }
      .tier-titan { background: rgba(255, 184, 48, 0.2); color: #ffb830; border: 1px solid #ffb830; }
      .tier-supporter { background: rgba(0, 255, 136, 0.2); color: #00ff88; border: 1px solid #00ff88; }
      .info-box { background: #0d101d; border-radius: 12px; padding: 20px; text-align: left; border-left: 4px solid #00e5ff; margin-bottom: 25px; font-size: 13px; color: #a0a6b8; line-height: 1.8; }
      .info-box strong { color: #00ff88; }
      .btn-discord { display: flex; align-items: center; justify-content: center; gap: 10px; background: #5865F2; color: #ffffff; font-weight: 700; text-decoration: none; padding: 16px 24px; font-size: 15px; border-radius: 10px; box-shadow: 0 4px 20px rgba(88, 101, 242, 0.4); margin-bottom: 14px; }
      .btn-download { display: inline-block; background: transparent; color: #00e5ff; font-weight: 600; font-size: 13px; text-decoration: none; padding: 10px 16px; border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 8px; width: 100%; }
      .footer-note { font-size: 11px; color: #636b82; margin-top: 22px; }
    </style>
  </head>
  <body>
    <div class="card">
      <div class="shield-icon">🛡️</div>
      <div class="brand-title">TECH YOU GAMING</div>
      <div class="subtitle">Real Life RP Master Mod (v10.7.2)</div>
      
      <div class="badge">🔒 VERIFIED MEMBERS ONLY</div>

      <div class="tiers-box">
        <span class="tier-pill tier-legend">⚡ Tech You Legends ⚡</span>
        <span class="tier-pill tier-titan">⚡ Titans ⚡</span>
        <span class="tier-pill tier-supporter">⚡ Supporters ⚡</span>
      </div>
      
      <div class="info-box">
        <strong>🔑 How to Claim Your Activation Key:</strong><br>
        1. Join our Official <strong>TECH YOU Discord</strong> server.<br>
        2. Go to <strong>#🔑-claim-mod-key</strong> and enter your YouTube Handle / Link.<br>
        3. Our Automated Accountant verifies your Tier and issues your 30-Day Key!
      </div>

      <a href="${DISCORD_INVITE_URL}" target="_blank" class="btn-discord">
        Claim Key on Discord
      </a>

      <a href="${MOD_DOWNLOAD_URL}" target="_blank" class="btn-download">
        ⬇️ Download Mod Files (Google Drive)
      </a>

      <div class="footer-note">
        🛡️ Protected by TECH YOU Enterprise DRM • 1 Key = 1 PC Binding
      </div>
    </div>
  </body>
  </html>
  `;
}
