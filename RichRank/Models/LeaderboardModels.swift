import Foundation

nonisolated enum LeaderboardScope: String, Codable, Sendable, CaseIterable, Identifiable {
    case global
    case age

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .global: return "Global"
        case .age: return "My Age"
        }
    }
}

nonisolated struct LeaderboardEntry: Codable, Sendable, Identifiable, Equatable {
    let rank: Int
    let username: String
    let balance: Decimal
    let deltaPct: Double

    var id: String { "\(rank)-\(username)" }

    enum CodingKeys: String, CodingKey {
        case rank
        case username
        case balance
        case deltaPct = "delta_pct"
    }
}

nonisolated struct LeaderboardSnapshot: Codable, Sendable, Equatable {
    let scope: String
    let totalUsers: Int
    let entries: [LeaderboardEntry]

    enum CodingKeys: String, CodingKey {
        case scope
        case totalUsers = "total_users"
        case entries
    }
}

nonisolated struct LeaderboardMe: Codable, Sendable, Equatable {
    let rank: Int?
    let totalUsers: Int
    let balance: Decimal
    let previousBalance: Decimal
    let deltaAmount: Decimal
    let deltaPct: Double
    let scope: String

    enum CodingKeys: String, CodingKey {
        case rank
        case totalUsers = "total_users"
        case balance
        case previousBalance = "previous_balance"
        case deltaAmount = "delta_amount"
        case deltaPct = "delta_pct"
        case scope
    }
}
