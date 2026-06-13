use std::io::{self, Write};
use tokio::time::{sleep, Duration};

mod core;
use core::RegimeEngine;

#[tokio::main]
async fn main() {
    println!("High-Agent RS Termux v0.1 - Mathematical Theory + Regime Engine");
    println!("Optimized for Galaxy Z Fold7 / Lenovo Tab Pro");
    println!("");

    let mut engine = RegimeEngine::new();

    loop {
        print!(">> ");
        io::stdout().flush().unwrap();

        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        let input = input.trim();

        match input {
            "q" | "quit" | "exit" => {
                println!("Exiting...");
                break;
            }
            "s" | "switch" => {
                engine.simulate_deviation_and_switch().await;
                println!("Regime switched to: {}", engine.current_regime_name());
                println!("Objective value: {:.4}", engine.current_objective_value());
            }
            input if input.starts_with("t ") => {
                let task = input.strip_prefix("t ").unwrap_or("");
                println!("Processing task: {}", task);
                engine.process_task(task).await;
                println!("Current regime: {}", engine.current_regime_name());
                println!("Objective: {:.4}", engine.current_objective_value());
            }
            "status" | "st" => {
                println!("Current regime: {}", engine.current_regime_name());
                println!("Objective value: {:.4}", engine.current_objective_value());
            }
            _ => {
                println!("Commands: s (switch), t <task>, status, q (quit)");
            }
        }

        // Light background monitoring
        sleep(Duration::from_millis(100)).await;
    }
}