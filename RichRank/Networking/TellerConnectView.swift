import SwiftUI
@preconcurrency import WebKit

/// Result passed from JS after a successful enrollment.
///
/// Official Teller Connect only returns ``accessToken`` + metadata — not the
/// account ids. Leave ``accountId`` nil and the Rank API resolves every
/// checking/savings account via ``GET /accounts`` with developer mTLS.
nonisolated struct TellerEnrollment: Sendable {
    let accessToken: String
    var accountId: String?
    var institutionName: String?
    var lastFour: String?
    var subtype: String?
}

nonisolated enum TellerConnectResult: Sendable {
    case success(TellerEnrollment)
    case cancelled
    case failure(String)
}

/// SwiftUI sheet that hosts Teller Connect inside a WKWebView and dispatches
/// the enrollment payload back to the caller via `onResult`.
struct TellerConnectSheet: View {
    let applicationId: String
    let environment: String
    let onResult: (TellerConnectResult) -> Void

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack(alignment: .topTrailing) {
            TellerConnectWebView(
                applicationId: applicationId,
                environment: environment,
                onResult: { result in
                    onResult(result)
                    dismiss()
                }
            )

            Button {
                onResult(.cancelled)
                dismiss()
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(.black)
                    .padding(10)
                    .background(Circle().fill(Color.rankPillFill))
            }
            .padding(.top, 12)
            .padding(.trailing, 16)
        }
        .background(Color.rankBackground.ignoresSafeArea())
    }
}

private struct TellerConnectWebView: UIViewRepresentable {
    let applicationId: String
    let environment: String
    let onResult: (TellerConnectResult) -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(onResult: onResult)
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let userContent = WKUserContentController()
        userContent.add(context.coordinator, name: "teller")
        config.userContentController = userContent
        config.websiteDataStore = .nonPersistent()

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.scrollView.bounces = false
        webView.isInspectable = true
        context.coordinator.hostWebView = webView

        let html = makeHTML(applicationId: applicationId, environment: environment)
        webView.loadHTMLString(html, baseURL: URL(string: "https://teller.io"))
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKScriptMessageHandler, WKNavigationDelegate {
        let onResult: (TellerConnectResult) -> Void
        private var didResolve = false
        private weak var hostWebView: WKWebView?

        init(onResult: @escaping (TellerConnectResult) -> Void) {
            self.onResult = onResult
        }

        /// After the document (and sync `connect.js`) loads, open Connect from native so startup order
        /// matches Simulator/device WebKit more reliably than only an inline `open()` call.
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            guard webView === hostWebView else { return }
            webView.evaluateJavaScript(
                """
                (function () {
                  if (typeof window.__rankOpenConnect !== 'function') return 0;
                  window.__rankOpenConnect();
                  return 1;
                })();
                """
            ) { _, error in
                if let error {
                    #if DEBUG
                    print("TellerConnect: __rankOpenConnect dispatch: \(error.localizedDescription)")
                    #endif
                }
            }
        }

        func userContentController(
            _ controller: WKUserContentController,
            didReceive message: WKScriptMessage
        ) {
            guard message.name == "teller" else { return }

            let envelopeResult = parseEnvelope(message.body)
            let dict: [String: Any]
            switch envelopeResult {
            case .success(let d):
                dict = d
            case .failure(let reason):
                finish(.failure(reason))
                return
            }

            let type = dict["type"] as? String ?? ""
            switch type {
            case "success":
                switch unpackEnrollment(dict) {
                case .success(let enrollment):
                    finish(.success(enrollment))
                case .failure(let reason):
                    finish(.failure(reason))
                }

            case "exit", "cancel":
                finish(.cancelled)

            case "failure":
                let msg = dict["message"] as? String ?? "Teller Connect failed"
                finish(.failure(msg))

            default:
                let label = type.isEmpty ? "(empty)" : type
                finish(.failure(
                    "Unexpected message from Connect (type: \(label)). Close and try again."
                ))
            }
        }

        /// Parse `postMessage` body: prefers JSON **string** (stable across WK versions), falls back to dict.
        private func parseEnvelope(_ body: Any) -> Result<[String: Any], String> {
            if let str = body as? String {
                guard let data = str.data(using: .utf8) else {
                    return .failure("Native bridge payload was not valid UTF-8")
                }
                do {
                    let obj = try JSONSerialization.jsonObject(with: data, options: [])
                    guard let map = obj as? [String: Any] else {
                        return .failure(
                            "Native bridge JSON was not an object — try restarting the sheet"
                        )
                    }
                    return .success(map)
                } catch {
                    return .failure("Malformed native bridge JSON: \(error.localizedDescription)")
                }
            }
            if let d = body as? [String: Any] {
                return .success(d)
            }
            if let nested = body as? [AnyHashable: Any] {
                var out: [String: Any] = [:]
                for (k, v) in nested {
                    if let key = k as? String {
                        out[key] = v
                    }
                }
                return out.isEmpty
                    ? .failure("Could not read native bridge message (unrecognized dictionary keys)")
                    : .success(out)
            }
            return .failure(
                "Could not read native bridge message (expected JSON string or object)"
            )
        }

        private func unpackEnrollment(_ envelope: [String: Any])
            -> Result<TellerEnrollment, String>
        {
            if let jsonStr = envelope["payload_json"] as? String {
                return parseEnrollmentJSONString(jsonStr)
            }
            if let nested = envelope["payload"] as? [String: Any] {
                return parseEnrollmentObject(nested)
            }
            return .failure(
                "Connect reported success but the native envelope had no enrollment data"
            )
        }

        private func parseEnrollmentJSONString(_ jsonUtf8: String)
            -> Result<TellerEnrollment, String>
        {
            guard let data = jsonUtf8.data(using: .utf8) else {
                return .failure("Enrollment JSON was not valid UTF-8")
            }
            do {
                let obj = try JSONSerialization.jsonObject(with: data, options: [])
                guard var map = obj as? [String: Any] else {
                    return .failure("Malformed enrollment JSON: root was not an object")
                }
                if enrollmentAccessToken(in: map) == nil {
                    if let inner = map["payload"] as? [String: Any] {
                        map = inner
                    } else if let inner = map["data"] as? [String: Any] {
                        map = inner
                    }
                }
                return parseEnrollmentObject(map)
            } catch {
                return .failure("Malformed enrollment JSON: \(error.localizedDescription)")
            }
        }

        private func enrollmentAccessToken(in map: [String: Any]) -> String? {
            accessTokenString(map["accessToken"]) ?? accessTokenString(map["access_token"])
        }

        private func accessTokenString(_ obj: Any?) -> String? {
            guard let obj else { return nil }
            if let s = obj as? String {
                let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
                return t.isEmpty ? nil : t
            }
            if let n = obj as? NSNumber {
                let s = n.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
                return s.isEmpty ? nil : s
            }
            let s = String(describing: obj).trimmingCharacters(in: .whitespacesAndNewlines)
            return s.isEmpty ? nil : s
        }

        private func parseEnrollmentObject(_ p: [String: Any])
            -> Result<TellerEnrollment, String>
        {
            func str(_ obj: Any?) -> String? {
                guard let obj else { return nil }
                if let s = obj as? String {
                    let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
                    return t.isEmpty ? nil : t
                }
                return accessTokenString(obj)
            }

            guard let token = enrollmentAccessToken(in: p) else {
                return .failure("Connect succeeded but enrollment JSON was missing accessToken")
            }

            var institutionName: String?
            if let enr = p["enrollment"] as? [String: Any],
               let inst = enr["institution"] as? [String: Any],
               let name = str(inst["name"]) {
                institutionName = name
            }

            let accounts = (p["accounts"] as? [[String: Any]]) ?? []
            let single = p["account"] as? [String: Any]

            func isDepository(_ acc: [String: Any]) -> Bool {
                let tp = (
                    acc["type"] as? String ??
                        acc["account_type"] as? String ??
                        ""
                ).lowercased()
                return tp == "depository"
            }

            let candidate: [String: Any]?
            if let first = accounts.first(where: { isDepository($0) }) {
                candidate = first
            } else if let single, isDepository(single) {
                candidate = single
            } else {
                candidate = accounts.first ?? single
            }

            var accountId: String?
            var lastFour: String?
            var subtype: String?

            if let acc = candidate {
                accountId = str(acc["id"])
                lastFour = str(acc["last_four"]) ?? str(acc["mask"])
                let st = (
                    acc["subtype"] as? String ??
                        acc["account_subtype"] as? String
                )?.lowercased()
                subtype = st
                if institutionName == nil,
                   let inst = acc["institution"] as? [String: Any],
                   let name = str(inst["name"]) {
                    institutionName = name
                }
            }

            let enrollment = TellerEnrollment(
                accessToken: token,
                accountId: accountId,
                institutionName: institutionName,
                lastFour: lastFour,
                subtype: subtype
            )
            return .success(enrollment)
        }

        private func finish(_ result: TellerConnectResult) {
            guard !didResolve else { return }
            didResolve = true
            onResult(result)
        }
    }
}

private func makeHTML(applicationId: String, environment: String) -> String {
    """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
      <style>
        html, body {
          margin: 0; padding: 0; height: 100%;
          background: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
        }
        #status { color: #666; padding: 24px; text-align: center; font-size: 14px; }
      </style>
    </head>
    <body>
      <div id="status">Loading bank connection…</div>
      <script src="https://cdn.teller.io/connect/connect.js"></script>
      <script>
        function sendEnvelope(obj) {
          var json = JSON.stringify(obj);
          try {
            window.webkit.messageHandlers.teller.postMessage(json);
          } catch (e) {
            try {
              window.webkit.messageHandlers.teller.postMessage(JSON.stringify({
                type: 'failure',
                message: (e && e.message) ? ('native bridge: ' + e.message) : 'native bridge failed'
              }));
            } catch (_) {}
          }
        }

        /* Teller docs: avoid async/defer on connect.js; placing the loader + boot
           at end of body means TellerConnect is defined before this block runs. */
        if (typeof TellerConnect === 'undefined') {
          sendEnvelope({ type: 'failure', message: 'Teller SDK failed to load' });
        } else {
          var connect = TellerConnect.setup({
            applicationId: \(jsString(applicationId)),
            environment: \(jsString(environment)),
            products: ['balance'],
            onInit: function() {
              var el = document.getElementById('status');
              if (el) el.innerText = '';
            },
            onSuccess: function(enrollment) {
              try {
                sendEnvelope({
                  type: 'success',
                  payload_json: JSON.stringify(enrollment)
                });
              } catch (e) {
                sendEnvelope({
                  type: 'failure',
                  message: (e && e.message) ? e.message : 'failed to serialize Teller enrollment'
                });
              }
            },
            onExit: function() { sendEnvelope({ type: 'exit' }); },
            onFailure: function(failure) {
              sendEnvelope({
                type: 'failure',
                message: (failure && failure.message) ? failure.message : 'Teller Connect failed'
              });
            }
          });
          window.__rankOpenConnect = function() {
            if (window.__rankOpenConnectDidRun) return;
            window.__rankOpenConnectDidRun = true;
            try { connect.open(); }
            catch (e) {
              sendEnvelope({
                type: 'failure',
                message: (e && e.message) ? e.message : 'connect.open failed'
              });
            }
          };
        }
      </script>
    </body>
    </html>
    """
}

private func jsString(_ s: String) -> String {
    let escaped = s
        .replacingOccurrences(of: "\\", with: "\\\\")
        .replacingOccurrences(of: "\"", with: "\\\"")
    return "\"\(escaped)\""
}
