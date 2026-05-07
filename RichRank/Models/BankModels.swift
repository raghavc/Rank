import Foundation

nonisolated struct ConnectTokenResponse: Codable, Sendable {
    let applicationId: String
    let environment: String
    let nonce: String?

    enum CodingKeys: String, CodingKey {
        case applicationId = "application_id"
        case environment
        case nonce
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
    let tellerAccessToken: String
    var tellerAccountId: String?
    var institutionName: String?
    var lastFour: String?
    var accountType: String?
    var accountSubtype: String?

    var tellerNonce: String?
    var tellerUserId: String?
    var tellerEnrollmentId: String?
    var tellerSignatures: [String]?

    enum CodingKeys: String, CodingKey {
        case tellerAccessToken = "teller_access_token"
        case tellerAccountId = "teller_account_id"
        case institutionName = "institution_name"
        case lastFour = "last_four"
        case accountType = "account_type"
        case accountSubtype = "account_subtype"
        case tellerNonce = "teller_nonce"
        case tellerUserId = "teller_user_id"
        case tellerEnrollmentId = "teller_enrollment_id"
        case tellerSignatures = "teller_signatures"
    }
}
