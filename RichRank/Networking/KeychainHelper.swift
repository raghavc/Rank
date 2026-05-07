import Foundation
import Security

enum KeychainHelper {
    private static let service = "com.BlackBeansInc.RichRank"
    private static let accessAccount = "rank.jwt"
    private static let refreshAccount = "rank.refresh"

    static func saveToken(_ token: String) {
        save(account: accessAccount, token: token)
    }

    static func loadToken() -> String? {
        load(account: accessAccount)
    }

    static func saveRefreshToken(_ token: String) {
        save(account: refreshAccount, token: token)
    }

    static func loadRefreshToken() -> String? {
        load(account: refreshAccount)
    }

    static func deleteToken() {
        delete(account: accessAccount)
        delete(account: refreshAccount)
    }

    private static func save(account: String, token: String) {
        let data = Data(token.utf8)
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(query as CFDictionary)
        var addQuery = query
        addQuery[kSecValueData as String] = data
        addQuery[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
        SecItemAdd(addQuery as CFDictionary, nil)
    }

    private static func load(account: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var item: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private static func delete(account: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
