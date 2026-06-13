use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Terminal,
};
use std::io;
use tokio::time::{sleep, Duration};

mod core;
mod tui;
mod optim;
mod skills;

use core::RegimeEngine;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut engine = RegimeEngine::new();

    let res = run_app(&mut terminal, &mut engine).await;

    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = res {
        println!("{:?}", err)
    }

    Ok(())
}

async fn run_app<B: ratatui::backend::Backend>(
    terminal: &mut Terminal<B>,
    engine: &mut RegimeEngine,
) -> io::Result<()> {
    loop {
        terminal.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(3),
                    Constraint::Min(10),
                    Constraint::Length(3),
                ])
                .split(f.size());

            let header = Paragraph::new("High-Agent RS v0.1 — Mathematical Theory + Regime Engine")
                .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
                .block(Block::default().borders(Borders::ALL).title("Status"));
            f.render_widget(header, chunks[0]);

            let current_regime = engine.current_regime_name();
            let objective = engine.current_objective_value();
            let content = vec![
                Line::from(vec![
                    Span::raw("Current Regime: "),
                    Span::styled(current_regime, Style::default().fg(Color::Green).add_modifier(Modifier::BOLD)),
                ]),
                Line::from(vec![
                    Span::raw("Objective Value: "),
                    Span::styled(format!("{:.4}", objective), Style::default().fg(Color::Yellow)),
                ]),
                Line::from(""),
                Line::from("Press 'q' to quit | 's' to simulate regime switch | 't' to send task to Ollama"),
            ];
            let main = Paragraph::new(content)
                .block(Block::default().borders(Borders::ALL).title("Live Graph & Regime State"));
            f.render_widget(main, chunks[1]);

            let footer = Paragraph::new("Optimized for RTX 5080 | Termux (phone/tablet) | Arch/Hyprland")
                .style(Style::default().fg(Color::Gray))
                .block(Block::default().borders(Borders::ALL));
            f.render_widget(footer, chunks[2]);
        })?;

        if event::poll(Duration::from_millis(200))? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') => return Ok(()),
                    KeyCode::Char('s') => {
                        engine.simulate_deviation_and_switch().await;
                    }
                    KeyCode::Char('t') => {
                        engine.process_task("Build a high-quality landing page").await;
                    }
                    _ => {}
                }
            }
        }

        sleep(Duration::from_millis(50)).await;
    }
}