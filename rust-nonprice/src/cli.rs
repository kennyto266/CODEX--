//! CLI tool for rust-nonprice
//!
//! This module provides a command-line interface for the rust-nonprice system.

use clap::{Parser, Subcommand};
use std::path::PathBuf;

/// CLI arguments
#[derive(Parser, Debug)]
#[command(name = "rust-nonprice")]
#[command(about = "High-performance non-price data technical indicators system")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Validate input data
    Validate {
        /// Path to input file (CSV or Parquet)
        input: PathBuf,
        /// Output validation report path (JSON)
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Calculate technical indicators
    Indicators {
        /// Path to input file
        input: PathBuf,
        /// Output path for indicators
        #[arg(short, long)]
        output: Option<PathBuf>,
        /// Specific indicator to calculate
        #[arg(short, long)]
        indicator: Option<String>,
    },
    /// Generate trading signals
    Signals {
        /// Path to indicators file
        indicators: PathBuf,
        /// Output path for signals
        output: PathBuf,
    },
    /// Optimize parameters
    Optimize {
        /// Path to indicators file
        indicators: PathBuf,
        /// Path to stock data file
        stock_data: PathBuf,
        /// Output path for results
        output: PathBuf,
    },
    /// Run backtest
    Backtest {
        /// Path to signals file
        signals: PathBuf,
        /// Path to stock data file
        stock_data: PathBuf,
    },
    /// Generate reports
    Report {
        /// Path to backtest results
        results: PathBuf,
        /// Output directory
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
}

/// Main entry point
fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Validate { input, output } => {
            println!("Validating data from: {:?}", input);
            println!("Output: {:?}", output);
        }
        Commands::Indicators {
            input,
            output,
            indicator,
        } => {
            println!("Calculating indicators from: {:?}", input);
            println!("Output: {:?}", output);
            println!("Indicator: {:?}", indicator);
        }
        Commands::Signals { indicators, output } => {
            println!("Generating signals from: {:?}", indicators);
            println!("Output: {:?}", output);
        }
        Commands::Optimize {
            indicators,
            stock_data,
            output,
        } => {
            println!("Optimizing parameters");
            println!("Indicators: {:?}", indicators);
            println!("Stock data: {:?}", stock_data);
            println!("Output: {:?}", output);
        }
        Commands::Backtest {
            signals,
            stock_data,
        } => {
            println!("Running backtest");
            println!("Signals: {:?}", signals);
            println!("Stock data: {:?}", stock_data);
        }
        Commands::Report { results, output } => {
            println!("Generating report from: {:?}", results);
            println!("Output: {:?}", output);
        }
    }
}
