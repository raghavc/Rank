import Foundation

nonisolated enum APIError: Error, LocalizedError, Sendable {
    case invalidURL
    case unauthorized
    case server(status: Int, message: String)
    case decoding(Error)
    case transport(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .unauthorized: return "Please log in again."
        case .server(let status, let message):
            if status >= 400 { return "[HTTP \(status)] \(message)" }
            return message
        case .decoding(let e): return "Decoding error: \(e.localizedDescription)"
        case .transport(let e): return e.localizedDescription
        }
    }
}

nonisolated private struct APIErrorBody: Decodable, Sendable {
    let detail: String?
}

/// Thread-safe formatters used by the API client. Each call gets a fresh
/// formatter to avoid capturing non-Sendable state across isolation domains.
nonisolated private enum DateCoding {
    static var iso: ISO8601DateFormatter {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }

    static var dateOnly: DateFormatter {
        let f = DateFormatter()
        f.calendar = Calendar(identifier: .iso8601)
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        f.timeZone = TimeZone(identifier: "UTC")
        return f
    }
}

actor APIClient {
    static let shared = APIClient()

    private let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private var token: String?

    init(baseURL: URL? = nil, session: URLSession? = nil) {
        let resolved: URL
        if let baseURL {
            resolved = baseURL
        } else {
            resolved = Self.resolveBaseURL(fromPlist: Bundle.main.object(forInfoDictionaryKey: "RankAPIBaseURL") as? String)
        }
        self.baseURL = resolved
#if DEBUG
        print("Rank API base URL: \(resolved.absoluteString)")
#endif
        if let session {
            self.session = session
        } else {
            let config = URLSessionConfiguration.default
            config.timeoutIntervalForRequest = 12
            config.timeoutIntervalForResource = 20
            self.session = URLSession(configuration: config)
        }

        let dec = JSONDecoder()
        let enc = JSONEncoder()

        enc.dateEncodingStrategy = .custom { date, encoder in
            var c = encoder.singleValueContainer()
            try c.encode(DateCoding.dateOnly.string(from: date))
        }
        dec.dateDecodingStrategy = .custom { decoder in
            let c = try decoder.singleValueContainer()
            let s = try c.decode(String.self)
            if let d = DateCoding.dateOnly.date(from: s) { return d }
            if let d = DateCoding.iso.date(from: s) { return d }
            throw DecodingError.dataCorruptedError(in: c, debugDescription: "bad date \(s)")
        }
        self.decoder = dec
        self.encoder = enc
    }

    /// Picks the API base URL from Info.plist (`RankAPIBaseURL`), with safe fallbacks when the
    /// value is empty, unparsed, or still contains an unexpanded `$(BUILD_SETTING)` placeholder.
    private static func resolveBaseURL(fromPlist raw: String?) -> URL {
        let resolved: URL
        if let raw {
            let str = raw.trimmingCharacters(in: .whitespacesAndNewlines)
            if !str.isEmpty,
               !str.contains("$("),
               let url = URL(string: str),
               url.host != nil {
                resolved = url
            } else {
                resolved = fallbackBaseURL()
            }
        } else {
            resolved = fallbackBaseURL()
        }
#if DEBUG
        return normalizeLoopbackDevPort(resolved)
#else
        return resolved
#endif
    }

    private static func fallbackBaseURL() -> URL {
#if DEBUG
        URL(string: "http://127.0.0.1:8000")!
#else
        URL(string: "http://98.84.78.7:8000")!
#endif
    }

    /// Debug Docker API listens on :8000. Misconfigured xcconfig used to truncate URLs at `//`,
    /// yielding `http://localhost` (port 80) — repair common mistakes.
    private static func normalizeLoopbackDevPort(_ url: URL) -> URL {
        guard let host = url.host?.lowercased() else { return url }
        guard host == "localhost" || host == "127.0.0.1" else { return url }
        guard url.scheme?.lowercased() == "http" else { return url }
        let port = url.port
        if port == nil || port == 80 {
            guard var c = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return url }
            c.port = 8000
            return c.url ?? url
        }
        return url
    }

    func setToken(_ token: String?) {
        self.token = token
    }

    func currentToken() -> String? { token }

    // MARK: - Auth

    func signup(username: String, email: String, password: String, dob: Date) async throws -> TokenResponse {
        struct Body: Encodable {
            let username: String
            let email: String
            let password: String
            let dob: Date
        }
        return try await request(
            "/auth/signup",
            method: "POST",
            body: Body(username: username, email: email, password: password, dob: dob),
            authed: false
        )
    }

    func login(email: String, password: String) async throws -> TokenResponse {
        struct Body: Encodable { let email: String; let password: String }
        return try await request(
            "/auth/login",
            method: "POST",
            body: Body(email: email, password: password),
            authed: false
        )
    }

    func refresh(refreshToken: String) async throws -> TokenResponse {
        struct Body: Encodable {
            let refresh_token: String
        }
        return try await request(
            "/auth/refresh",
            method: "POST",
            body: Body(refresh_token: refreshToken),
            authed: false
        )
    }

    func logout(refreshToken: String? = nil) async throws {
        struct Body: Encodable {
            let refresh_token: String?
        }
        let bodyData = try encoder.encode(Body(refresh_token: refreshToken))
        let _: EmptyResponse = try await performRequest(
            path: "/auth/logout",
            method: "POST",
            bodyData: bodyData,
            authed: true
        )
    }

    func me() async throws -> Me {
        try await request("/auth/me", method: "GET")
    }

    func deleteMe() async throws {
        try await requestVoid("/auth/me", method: "DELETE")
    }

    // MARK: - Bank

    func connectToken() async throws -> ConnectTokenResponse {
        try await request("/bank/connect-token", method: "POST")
    }

    func linkBank(_ body: BankLinkRequest) async throws -> BankAccount {
        try await request("/bank/link", method: "POST", body: body)
    }

    func listAccounts() async throws -> [BankAccount] {
        try await request("/bank/accounts", method: "GET")
    }

    func disconnect(accountId: UUID) async throws {
        try await requestVoid("/bank/\(accountId.uuidString)", method: "DELETE")
    }

    // MARK: - Leaderboard

    func leaderboardMe(scope: LeaderboardScope) async throws -> LeaderboardMe {
        try await request("/leaderboard/me?scope=\(scope.rawValue)", method: "GET")
    }

    func leaderboard(scope: LeaderboardScope, limit: Int = 50) async throws -> LeaderboardSnapshot {
        try await request("/leaderboard?scope=\(scope.rawValue)&limit=\(limit)", method: "GET")
    }

    // MARK: - Core request

    private func request<T: Decodable>(
        _ path: String,
        method: String,
        authed: Bool = true
    ) async throws -> T {
        try await performRequest(path: path, method: method, bodyData: nil, authed: authed)
    }

    private func request<T: Decodable, B: Encodable>(
        _ path: String,
        method: String,
        body: B,
        authed: Bool = true
    ) async throws -> T {
        let data = try encoder.encode(body)
        return try await performRequest(path: path, method: method, bodyData: data, authed: authed)
    }

    private func requestVoid(_ path: String, method: String, authed: Bool = true) async throws {
        let _: EmptyResponse = try await performRequest(
            path: path, method: method, bodyData: nil, authed: authed
        )
    }

    private struct EmptyResponse: Decodable {}

    private func performRequest<T: Decodable>(
        path: String,
        method: String,
        bodyData: Data?,
        authed: Bool
    ) async throws -> T {
        guard let url = URL(string: path, relativeTo: baseURL) else { throw APIError.invalidURL }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        if authed, let token {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let bodyData {
            req.httpBody = bodyData
        }

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: req)
        } catch {
            throw APIError.transport(error)
        }

        guard let http = response as? HTTPURLResponse else {
            throw APIError.server(status: -1, message: "Bad response")
        }

        if http.statusCode == 401 {
            throw APIError.unauthorized
        }
        guard (200..<300).contains(http.statusCode) else {
            let detail = (try? decoder.decode(APIErrorBody.self, from: data))?.detail
                ?? String(data: data, encoding: .utf8)
                ?? "Server error"
            throw APIError.server(status: http.statusCode, message: detail)
        }

        if T.self == EmptyResponse.self, data.isEmpty || http.statusCode == 204 {
            return EmptyResponse() as! T
        }
        if data.isEmpty {
            // For non-empty types we should never get here, but guard anyway.
            throw APIError.server(status: http.statusCode, message: "Empty response body")
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }
}
