import Foundation

private enum LeaderboardDecoding {
    static func decimal<Key: CodingKey>(
        from container: KeyedDecodingContainer<Key>,
        forKey key: Key
    ) throws -> Decimal {
        if let decimal = try? container.decode(Decimal.self, forKey: key) {
            return decimal
        }
        if let string = try? container.decode(String.self, forKey: key),
           let decimal = Decimal(string: string, locale: Locale(identifier: "en_US_POSIX")) {
            return decimal
        }
        if let double = try? container.decode(Double.self, forKey: key) {
            return Decimal(double)
        }
        if let int = try? container.decode(Int.self, forKey: key) {
            return Decimal(int)
        }
        throw DecodingError.dataCorruptedError(
            forKey: key,
            in: container,
            debugDescription: "Expected decimal as number or string"
        )
    }
}

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
    let previousRank: Int?
    let username: String
    let balance: Decimal
    let deltaPct: Double

    var id: String { "\(rank)-\(username)" }

    enum CodingKeys: String, CodingKey {
        case rank
        case previousRank = "previous_rank"
        case username
        case balance
        case deltaPct = "delta_pct"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        rank = try container.decode(Int.self, forKey: .rank)
        previousRank = try container.decodeIfPresent(Int.self, forKey: .previousRank)
        username = try container.decode(String.self, forKey: .username)
        balance = try LeaderboardDecoding.decimal(from: container, forKey: .balance)
        deltaPct = try container.decode(Double.self, forKey: .deltaPct)
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
    let previousRank: Int?
    let totalUsers: Int
    let balance: Decimal
    let previousBalance: Decimal
    let deltaAmount: Decimal
    let deltaPct: Double
    let scope: String

    enum CodingKeys: String, CodingKey {
        case rank
        case previousRank = "previous_rank"
        case totalUsers = "total_users"
        case balance
        case previousBalance = "previous_balance"
        case deltaAmount = "delta_amount"
        case deltaPct = "delta_pct"
        case scope
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        rank = try container.decodeIfPresent(Int.self, forKey: .rank)
        previousRank = try container.decodeIfPresent(Int.self, forKey: .previousRank)
        totalUsers = try container.decode(Int.self, forKey: .totalUsers)
        balance = try LeaderboardDecoding.decimal(from: container, forKey: .balance)
        previousBalance = try LeaderboardDecoding.decimal(from: container, forKey: .previousBalance)
        deltaAmount = try LeaderboardDecoding.decimal(from: container, forKey: .deltaAmount)
        deltaPct = try container.decode(Double.self, forKey: .deltaPct)
        scope = try container.decode(String.self, forKey: .scope)
    }
}
