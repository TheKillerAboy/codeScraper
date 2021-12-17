use std::fs;
use crate::Result;

pub fn path() -> Result<std::path::PathBuf>{
    Ok(std::path::Path::new("/etc").join("config.yaml"))
}

pub fn get() -> Result<serde_yaml::Value>{
    let buf = fs::read_to_string(path()?)?;
    let doc = serde_yaml::from_str(&buf)?;

    Ok(doc)
}

pub fn set(yaml: serde_yaml::Value) -> Result<()>{
    let s = serde_yaml::to_string(&yaml)?;
    fs::write(path()?,&s)?;

    Ok(())
}