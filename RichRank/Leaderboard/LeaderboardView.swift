import SwiftUI

struct LeaderboardView: View {
    @Environment(AppState.self) private var app
    @State private var scope: LeaderboardScope = .global
    @State private var showSettings = false
    @State private var countdown = RefreshCountdown()
    private let tickerThreshold = 10

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if let err = app.leaderboardBannerError(for: scope) {
                    Text(err)
                        .font(.rankCaption)
                        .foregroundStyle(Color.rankCoral)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 20)
                        .padding(.bottom, 8)
                }

                LeaderboardToggle(scope: $scope)
                    .padding(.horizontal, 20)
                    .padding(.top, 8)
                    .padding(.bottom, 8)

                if let me = app.me, let mine = app.mine(for: scope) {
                    MyRankCard(username: me.username, me: mine)
                        .padding(.horizontal, 20)
                        .padding(.bottom, 4)
                }

                contentList
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            }
            .background(Color.rankTerminalCanvas.ignoresSafeArea())
            .navigationTitle("Rank")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(Color.rankTerminalCanvas, for: .navigationBar)
            .toolbarColorScheme(.light, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Text(countdown.text)
                        .font(.system(size: 12, weight: .semibold, design: .monospaced))
                        .foregroundStyle(.black)
                        .monospacedDigit()
                        .fixedSize()
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                            .foregroundStyle(Color.rankTerminalText)
                    }
                }
            }
            .sheet(isPresented: $showSettings) {
                NavigationStack { SettingsView() }
            }
            .task { await app.refresh(scope: scope) }
            .onChange(of: scope) { _, new in
                Task { await app.refresh(scope: new) }
            }
        }
    }

    @ViewBuilder
    private var contentList: some View {
        if let snap = app.snapshot(for: scope) {
            if snap.entries.isEmpty {
                ScrollView {
                    emptyState
                        .frame(maxWidth: .infinity, minHeight: 280)
                }
                .scrollIndicators(.hidden)
                .refreshable { await app.refresh(scope: scope) }
            } else if snap.entries.count < tickerThreshold {
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        terminalColumnHeader
                            .padding(.top, 2)
                            .padding(.bottom, 2)

                        TerminalTickerScroll(
                            entries: snap.entries,
                            highlightUsername: app.me?.username,
                            threshold: tickerThreshold
                        )
                        .frame(maxWidth: .infinity)
                    }
                }
                .scrollIndicators(.hidden)
                .refreshable { await app.refresh(scope: scope) }
            } else {
                VStack(alignment: .leading, spacing: 0) {
                    terminalColumnHeader
                        .padding(.top, 2)
                        .padding(.bottom, 2)

                    TerminalTickerScroll(
                        entries: snap.entries,
                        highlightUsername: app.me?.username,
                        threshold: tickerThreshold
                    )
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            }
        } else {
            ScrollView {
                ProgressView()
                    .frame(maxWidth: .infinity, minHeight: 280)
            }
            .scrollIndicators(.hidden)
            .refreshable { await app.refresh(scope: scope) }
        }
    }

    private var terminalColumnHeader: some View {
        HStack(spacing: 10) {
            Color.clear
                .frame(width: LeaderboardTerminalColumns.movementWidth)

            Text("RANK")
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundStyle(Color.rankTerminalText.opacity(0.55))
                .tracking(0.8)
                .frame(width: LeaderboardTerminalColumns.rankWidth, alignment: .trailing)

            Text("USERNAME")
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundStyle(Color.rankTerminalText.opacity(0.55))
                .tracking(0.8)

            Text("|")
                .font(.system(size: 10, weight: .regular, design: .monospaced))
                .foregroundStyle(Color.rankTerminalRule)

            Spacer(minLength: 8)

            Text("BALANCE")
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundStyle(Color.rankTerminalText.opacity(0.55))
                .tracking(0.8)
        }
        .padding(.horizontal, 16)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(Color.rankTerminalRule)
                .frame(height: 1)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 10) {
            Spacer()
            Text("Nobody on the board yet.")
                .font(.system(size: 15, weight: .semibold, design: .monospaced))
                .foregroundStyle(Color.rankTerminalText.opacity(0.55))
            Text("Hold tight — the daily refresh runs at 8am ET.")
                .font(.rankCaption)
                .foregroundStyle(Color.rankTerminalText.opacity(0.45))
            Spacer()
        }
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    LeaderboardView().environment(AppState())
}
