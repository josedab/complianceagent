/**
 * ComplianceAgent TypeScript SDK Example
 *
 * Demonstrates how to interact with the ComplianceAgent API from TypeScript.
 * Covers common workflows including:
 * - Authentication
 * - Managing regulations and repositories
 * - Running compliance scans
 * - Processing compliance fixes
 * - Audit trail access
 * - Chat integration
 *
 * Prerequisites:
 *     npm install node-fetch dotenv
 *
 * Environment:
 *     Set COMPLIANCEAGENT_API_URL and COMPLIANCEAGENT_API_KEY in your environment
 *     or create a .env file.
 */

import "dotenv/config";

// ---------- Types ----------

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface Regulation {
  id: string;
  name: string;
  framework: string;
  jurisdiction: string;
  status: string;
}

interface Requirement {
  id: string;
  reference_id: string;
  title: string;
  description: string;
  category: string;
  obligation_type: string;
}

interface Repository {
  id: string;
  name: string;
  url: string;
  status: string;
  compliance_score?: number;
}

interface ComplianceStatus {
  overall_score: number;
  frameworks: Array<{ name: string; score: number }>;
}

interface AuditEntry {
  id: string;
  event_type: string;
  event_description: string;
  created_at: string;
  actor_type: string;
}

interface ChainVerification {
  valid: boolean;
  entries_checked: number;
  invalid_entries: string[];
}

interface ChatMessage {
  id: string;
  conversation_id: string;
  content: string;
  citations: Array<{ source: string; title: string }>;
}

// ---------- Client ----------

class ComplianceAgentClient {
  private baseUrl: string;
  private apiKey: string;
  private timeout: number;

  constructor(options?: {
    baseUrl?: string;
    apiKey?: string;
    timeout?: number;
  }) {
    this.baseUrl = (
      options?.baseUrl ||
      process.env.COMPLIANCEAGENT_API_URL ||
      "http://localhost:8000"
    ).replace(/\/$/, "");
    this.apiKey = options?.apiKey || process.env.COMPLIANCEAGENT_API_KEY || "";
    this.timeout = options?.timeout ?? 30000;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: Record<string, unknown>
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await response.text().catch(() => "");
        throw new ComplianceAgentError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorBody
        );
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  }

  // --- Health ---

  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.request("GET", "/health");
  }

  // --- Authentication ---

  async login(
    email: string,
    password: string
  ): Promise<AuthTokens> {
    return this.request("POST", "/api/v1/auth/login", { email, password });
  }

  async register(
    email: string,
    password: string,
    fullName: string
  ): Promise<{ id: string; email: string }> {
    return this.request("POST", "/api/v1/auth/register", {
      email,
      password,
      full_name: fullName,
    });
  }

  async logout(): Promise<void> {
    await this.request("POST", "/api/v1/auth/logout", {});
  }

  async forgotPassword(email: string): Promise<{ message: string }> {
    return this.request("POST", "/api/v1/auth/forgot-password", { email });
  }

  async resetPassword(
    token: string,
    newPassword: string
  ): Promise<{ message: string }> {
    return this.request("POST", "/api/v1/auth/reset-password", {
      token,
      new_password: newPassword,
    });
  }

  // --- Settings & Profile ---

  async getProfile(): Promise<{
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
  }> {
    return this.request("GET", "/api/v1/settings/profile");
  }

  async updateProfile(data: {
    full_name?: string;
    email?: string;
  }): Promise<{ id: string; email: string; full_name: string }> {
    return this.request("PATCH", "/api/v1/settings/profile", data);
  }

  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<{ message: string }> {
    return this.request("POST", "/api/v1/settings/password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  async getNotificationPreferences(): Promise<Record<string, unknown>> {
    return this.request("GET", "/api/v1/settings/notifications");
  }

  async updateNotificationPreferences(
    prefs: Record<string, unknown>
  ): Promise<Record<string, unknown>> {
    return this.request("PUT", "/api/v1/settings/notifications", prefs);
  }

  // --- API Keys ---

  async listApiKeys(): Promise<{
    items: Array<{ id: string; name: string; prefix: string; scopes: string[] }>;
    total: number;
  }> {
    return this.request("GET", "/api/v1/api-keys");
  }

  async createApiKey(
    name: string,
    scopes?: string[]
  ): Promise<{ id: string; name: string; key: string; prefix: string }> {
    return this.request("POST", "/api/v1/api-keys", { name, scopes });
  }

  async revokeApiKey(keyId: string): Promise<{ message: string }> {
    return this.request("DELETE", `/api/v1/api-keys/${keyId}`);
  }

  // --- Regulations ---

  async listRegulations(filters?: {
    framework?: string;
    jurisdiction?: string;
  }): Promise<Regulation[]> {
    const params = new URLSearchParams();
    if (filters?.framework) params.set("framework", filters.framework);
    if (filters?.jurisdiction)
      params.set("jurisdiction", filters.jurisdiction);
    const qs = params.toString();
    return this.request("GET", `/api/v1/regulations${qs ? `?${qs}` : ""}`);
  }

  async getRegulation(regulationId: string): Promise<Regulation> {
    return this.request("GET", `/api/v1/regulations/${regulationId}`);
  }

  async getRequirements(
    regulationId: string,
    filters?: { category?: string; obligation_type?: string }
  ): Promise<Requirement[]> {
    const params = new URLSearchParams();
    if (filters?.category) params.set("category", filters.category);
    if (filters?.obligation_type)
      params.set("obligation_type", filters.obligation_type);
    const qs = params.toString();
    return this.request(
      "GET",
      `/api/v1/regulations/${regulationId}/requirements${qs ? `?${qs}` : ""}`
    );
  }

  // --- Repositories ---

  async listRepositories(): Promise<Repository[]> {
    return this.request("GET", "/api/v1/repositories");
  }

  async addRepository(url: string, name: string): Promise<Repository> {
    return this.request("POST", "/api/v1/repositories", { url, name });
  }

  async analyzeRepository(
    repositoryId: string
  ): Promise<{ task_id: string; status: string }> {
    return this.request(
      "POST",
      `/api/v1/repositories/${repositoryId}/analyze`
    );
  }

  // --- Compliance ---

  async getComplianceStatus(): Promise<ComplianceStatus> {
    return this.request("GET", "/api/v1/compliance/status");
  }

  async generateComplianceCode(
    mappingId: string
  ): Promise<{ files: Array<{ path: string; content: string }> }> {
    return this.request("POST", "/api/v1/compliance/generate", {
      mapping_id: mappingId,
    });
  }

  // --- Audit ---

  async listAuditEntries(filters?: {
    event_type?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<AuditEntry[]> {
    const params = new URLSearchParams();
    if (filters?.event_type) params.set("event_type", filters.event_type);
    if (filters?.start_date) params.set("start_date", filters.start_date);
    if (filters?.end_date) params.set("end_date", filters.end_date);
    const qs = params.toString();
    return this.request("GET", `/api/v1/audit/${qs ? `?${qs}` : ""}`);
  }

  async verifyAuditChain(): Promise<ChainVerification> {
    return this.request("GET", "/api/v1/audit/verify-chain");
  }

  // --- Chat ---

  async sendChatMessage(
    message: string,
    options?: {
      conversation_id?: string;
      regulations?: string[];
      include_code_context?: boolean;
    }
  ): Promise<ChatMessage> {
    return this.request("POST", "/api/v1/chat/message", {
      message,
      ...options,
    });
  }

  // --- IDE Integration ---

  async analyzeDocument(
    content: string,
    language: string,
    filePath?: string
  ): Promise<{
    diagnostics: Array<{
      rule: string;
      severity: string;
      message: string;
      line: number;
    }>;
  }> {
    return this.request("POST", "/api/v1/ide/analyze", {
      content,
      language,
      file_path: filePath,
    });
  }

  async getQuickFix(
    content: string,
    language: string,
    rule: string,
    line: number
  ): Promise<{ fixed_code: string; explanation: string }> {
    return this.request("POST", "/api/v1/ide/quickfix", {
      content,
      language,
      rule,
      line,
    });
  }
}

// ---------- Error class ----------

class ComplianceAgentError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public responseBody: string
  ) {
    super(message);
    this.name = "ComplianceAgentError";
  }
}

// ---------- Example usage ----------

async function main(): Promise<void> {
  const client = new ComplianceAgentClient();

  // 1. Health check
  console.log("=== Health Check ===");
  try {
    const health = await client.healthCheck();
    console.log(`Status: ${health.status}, Version: ${health.version}`);
  } catch (err) {
    console.error("Server not reachable:", (err as Error).message);
    return;
  }

  // 2. List regulations
  console.log("\n=== Regulations ===");
  try {
    const regulations = await client.listRegulations({ framework: "gdpr" });
    for (const reg of regulations) {
      console.log(`  ${reg.name} (${reg.framework}) - ${reg.jurisdiction}`);
    }
  } catch (err) {
    console.error("Failed to list regulations:", (err as Error).message);
  }

  // 3. List repositories and check compliance
  console.log("\n=== Repositories ===");
  try {
    const repos = await client.listRepositories();
    for (const repo of repos) {
      console.log(`  ${repo.name}: ${repo.status}`);
    }
  } catch (err) {
    console.error("Failed to list repositories:", (err as Error).message);
  }

  // 4. Check compliance status
  console.log("\n=== Compliance Status ===");
  try {
    const status = await client.getComplianceStatus();
    console.log(`  Overall score: ${status.overall_score}%`);
    for (const fw of status.frameworks) {
      console.log(`  ${fw.name}: ${fw.score}%`);
    }
  } catch (err) {
    console.error("Failed to get status:", (err as Error).message);
  }

  // 5. Verify audit chain
  console.log("\n=== Audit Chain Verification ===");
  try {
    const verification = await client.verifyAuditChain();
    console.log(
      `  Valid: ${verification.valid}, Entries: ${verification.entries_checked}`
    );
  } catch (err) {
    console.error("Failed to verify chain:", (err as Error).message);
  }

  // 6. Chat with compliance assistant
  console.log("\n=== Compliance Chat ===");
  try {
    const response = await client.sendChatMessage(
      "What encryption does HIPAA require?",
      { regulations: ["HIPAA"] }
    );
    console.log(`  Response: ${response.content.substring(0, 200)}...`);
    if (response.citations.length > 0) {
      console.log(`  Citations: ${response.citations.map((c) => c.title).join(", ")}`);
    }
  } catch (err) {
    console.error("Failed to chat:", (err as Error).message);
  }
}

main().catch(console.error);
