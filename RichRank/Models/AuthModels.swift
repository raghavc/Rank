import Foundation

nonisolated struct TokenResponse: Codable, Sendable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let tokenType: String
    let username: String
    let ageBucket: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
        case username
        case ageBucket = "age_bucket"
    }
}

nonisolated struct Me: Codable, Sendable, Equatable {
    let username: String
    let ageBucket: String
    let hasBankLinked: Bool

    enum CodingKeys: String, CodingKey {
        case username
        case ageBucket = "age_bucket"
        case hasBankLinked = "has_bank_linked"
    }
}
