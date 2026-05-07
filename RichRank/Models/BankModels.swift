import Foundation

nonisolated struct ConnectTokenResponse: Codable, Sendable {
    let applicationId: String
    let environment: String

    enum CodingKeys: String, CodingKey {
        case applicationId = "application_id"
        case environment
    }
}

nonisolated struct BankAccount: Codable, Sendable, Identifiable, Equatable {
    let id: UUID
    let institutionName: String?
    let accountSubtype: String?
    let lastFour: String?
    let isActive: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case institutionName = "institution_name"
        case accountSubtype = "account_subtype"
        case lastFour = "last_four"
        case isActive = "is_active"
    }
}

nonisolated struct BankLinkRequest: Codable, Sendable {
    /// A Teller OAuth access token (from Connect `onSuccess`).
    let tellerAccessToken: String

    /// If omitted / `nil`, Rank calls Teller ``GET /accounts`` with developer mTLS
    /// from the backend and stores every enrolled checking/savings account.
    var tellerAccountId: String?
    var institutionName: String?
    var lastFour: String?

    /// Always `"depository"` when you already know ``tellerAccountId``. Leave unset
    /// for server-side enumeration.
    var accountType: String?

    /// Required only when linking a specific ``tellerAccountId`` client-side.
    var accountSubtype: String?

    enum CodingKeys: String, CodingKey {
        case tellerAccessToken = "teller_access_token"
        case tellerAccountId = "teller_account_id"
        case institutionName = "institution_name"
        case lastFour = "last_four"
        case accountType = "account_type"
        case accountSubtype = "account_subtype"
    }
}

