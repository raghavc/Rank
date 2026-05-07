import Foundation
import Observation

enum Route: Equatable {
    case welcome
    case signup
    case login
    case connectBank
    case leaderboard
}

@Observable
@MainActor
final class AppState {
    var route: Route = .welcome
    var me: Me?
    var linkedAccounts: [BankAccount] = []
    var globalBoard: LeaderboardSnapshot?
    var ageBoard: LeaderboardSnapshot?
    var meGlobal: LeaderboardMe?
    var meAge: LeaderboardMe?

    var lastError: String?

    private let api = APIClient.shared

    init() {}

    func bootstrap() async {
        if let token = KeychainHelper.loadToken() {
            await api.setToken(token)
            do {
                let me = try await api.me()
                self.me = me
                self.route = me.hasBankLinked ? .leaderboard : .connectBank
                if me.hasBankLinked {
                    await refreshLeaderboards()
                    await refreshLinkedAccounts()
                }
            } catch APIError.unauthorized {
                if let rt = KeychainHelper.loadRefreshToken() {
                    do {
                        let t = try await api.refresh(refreshToken: rt)
                        KeychainHelper.saveToken(t.accessToken)
                        KeychainHelper.saveRefreshToken(t.refreshToken)
                        await api.setToken(t.accessToken)
                        let me = try await api.me()
                        self.me = me
                        self.route = me.hasBankLinked ? .leaderboard : .connectBank
                        if me.hasBankLinked {
                            await refreshLeaderboards()
                            await refreshLinkedAccounts()
                        }
                    } catch {
                        await logout()
                    }
                } else {
                    await logout()
                }
            } catch {
                self.lastError = (error as? APIError)?.localizedDescription ?? error.localizedDescription
            }
        } else {
            self.route = .welcome
        }
    }

    // MARK: - Auth

    func signUp(username: String, email: String, password: String, dob: Date) async throws -> TokenResponse {
        let token = try await api.signup(username: username, email: email, password: password, dob: dob)
        KeychainHelper.saveToken(token.accessToken)
        KeychainHelper.saveRefreshToken(token.refreshToken)
        await api.setToken(token.accessToken)
        self.me = Me(username: token.username, ageBucket: token.ageBucket, hasBankLinked: false)
        return token
    }

    func logIn(email: String, password: String) async throws {
        let token = try await api.login(email: email, password: password)
        KeychainHelper.saveToken(token.accessToken)
        KeychainHelper.saveRefreshToken(token.refreshToken)
        await api.setToken(token.accessToken)
        let me = try await api.me()
        self.me = me
        self.route = me.hasBankLinked ? .leaderboard : .connectBank
        if me.hasBankLinked {
            await refreshLeaderboards()
            await refreshLinkedAccounts()
        }
    }

    func logout() async {
        try? await api.logout(refreshToken: nil)
        KeychainHelper.deleteToken()
        await api.setToken(nil)
        self.me = nil
        self.linkedAccounts = []
        self.globalBoard = nil
        self.ageBoard = nil
        self.meGlobal = nil
        self.meAge = nil
        self.route = .welcome
    }

    func deleteAccount() async throws {
        try await api.deleteMe()
        await logout()
    }

    // MARK: - Bank

    func linkBank(
        accessToken: String,
        accountId: String?,
        institutionName: String?,
        lastFour: String?,
        subtype: String?,
        tellerNonce: String?,
        tellerUserId: String?,
        tellerEnrollmentId: String?,
        tellerSignatures: [String]?
    ) async throws {
        let req = BankLinkRequest(
            tellerAccessToken: accessToken,
            tellerAccountId: accountId,
            institutionName: institutionName,
            lastFour: lastFour,
            accountType: accountId == nil ? nil : "depository",
            accountSubtype: subtype,
            tellerNonce: tellerNonce,
            tellerUserId: tellerUserId,
            tellerEnrollmentId: tellerEnrollmentId,
            tellerSignatures: tellerSignatures
        )
        _ = try await api.linkBank(req)
        if let me {
            self.me = Me(username: me.username, ageBucket: me.ageBucket, hasBankLinked: true)
        }
        self.route = .leaderboard
        await refreshLinkedAccounts()
        await refreshLeaderboards()
    }

    func refreshLinkedAccounts() async {
        do {
            self.linkedAccounts = try await api.listAccounts()
        } catch {
            self.lastError = (error as? APIError)?.localizedDescription ?? error.localizedDescription
        }
    }

    func disconnect(accountId: UUID) async {
        do {
            try await api.disconnect(accountId: accountId)
            await refreshLinkedAccounts()
            if linkedAccounts.isEmpty, let me {
                self.me = Me(username: me.username, ageBucket: me.ageBucket, hasBankLinked: false)
            }
        } catch {
            self.lastError = (error as? APIError)?.localizedDescription ?? error.localizedDescription
        }
    }

    // MARK: - Leaderboard

    func refreshLeaderboards() async {
        async let g: () = refresh(scope: .global)
        async let a: () = refresh(scope: .age)
        _ = await (g, a)
    }

    func refresh(scope: LeaderboardScope) async {
        do {
            lastError = nil
            let snap = try await api.leaderboard(scope: scope, limit: 100)
            let mine = try await api.leaderboardMe(scope: scope)
            switch scope {
            case .global:
                self.globalBoard = snap
                self.meGlobal = mine
            case .age:
                self.ageBoard = snap
                self.meAge = mine
            }
        } catch APIError.unauthorized {
            await logout()
        } catch {
            self.lastError = (error as? APIError)?.localizedDescription ?? error.localizedDescription
            let empty = LeaderboardSnapshot(scope: scope.rawValue, totalUsers: 0, entries: [])
            switch scope {
            case .global:
                if self.globalBoard == nil {
                    self.globalBoard = empty
                }
            case .age:
                if self.ageBoard == nil {
                    self.ageBoard = empty
                }
            }
        }
    }

    func leaderboardBannerError(for scope: LeaderboardScope) -> String? {
        guard snapshot(for: scope)?.entries.isEmpty == true else { return nil }
        guard let lastError else { return nil }
        if lastError.contains("[HTTP 500]") {
            return "Leaderboard is temporarily unavailable. Pull down to refresh."
        }
        if lastError.contains("[HTTP 429]") {
            return "You're refreshing too quickly. Wait a moment and try again."
        }
        return lastError
    }

    func snapshot(for scope: LeaderboardScope) -> LeaderboardSnapshot? {
        switch scope {
        case .global: return globalBoard
        case .age: return ageBoard
        }
    }

    func mine(for scope: LeaderboardScope) -> LeaderboardMe? {
        switch scope {
        case .global: return meGlobal
        case .age: return meAge
        }
    }
}
