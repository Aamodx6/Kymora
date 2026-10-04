#![deny(unsafe_code)]

//! Feature plan resolution and needs bitmask computation with multi-view invariance pruning.

use crate::error::KymoraError;
use crate::features::views;
use crate::intermediates::Needs;
use crate::registry::{self, ProfileMask, FEATURES};

#[derive(Clone, Debug)]
pub struct PlanItem {
    pub view: String,
    pub feature_idx: usize,
    pub output_name: String,
}

#[derive(Clone, Debug)]
pub struct FeaturePlan {
    pub indices: Vec<usize>,
    pub names: Vec<String>,
    pub needs: Needs,
    pub items: Vec<PlanItem>,
    pub views: Vec<String>,
}

impl FeaturePlan {
    /// Build a feature execution plan from profile or explicit feature list with default raw view.
    pub fn build<S: AsRef<str>>(
        profile: Option<&str>,
        features: Option<&[S]>,
    ) -> Result<Self, KymoraError> {
        Self::build_with_views(profile, features, None::<&[&str]>)
    }

    /// Build a feature execution plan across multiple views with invariance pruning.
    pub fn build_with_views<S: AsRef<str>, V: AsRef<str>>(
        profile: Option<&str>,
        features: Option<&[S]>,
        views: Option<&[V]>,
    ) -> Result<Self, KymoraError> {
        let mut base_indices = Vec::new();
        let mut base_needs = Needs::empty();

        if let Some(req_features) = features {
            for req in req_features {
                let s = req.as_ref();
                if let Some(idx) = registry::find_feature(s) {
                    let def = &FEATURES[idx];
                    base_indices.push(idx);
                    base_needs |= def.needs;
                } else {
                    return Err(KymoraError::UnknownFeature {
                        name: s.to_string(),
                    });
                }
            }
        } else {
            let prof = profile.unwrap_or("core33");
            match prof {
                "minimal" => {
                    for (idx, def) in FEATURES.iter().enumerate() {
                        if def.profiles.contains(ProfileMask::MINIMAL) {
                            base_indices.push(idx);
                            base_needs |= def.needs;
                        }
                    }
                }
                "core33" => {
                    let max_core = 33.min(FEATURES.len());
                    for idx in 0..max_core {
                        let def = &FEATURES[idx];
                        base_indices.push(idx);
                        base_needs |= def.needs;
                    }
                }
                "extended" => {
                    for (idx, def) in FEATURES.iter().enumerate() {
                        if def.profiles.contains(ProfileMask::EXTENDED) {
                            base_indices.push(idx);
                            base_needs |= def.needs;
                        }
                    }
                }
                "full" => {
                    for (idx, def) in FEATURES.iter().enumerate() {
                        if def.profiles.contains(ProfileMask::FULL) {
                            base_indices.push(idx);
                            base_needs |= def.needs;
                        }
                    }
                }
                _ => {
                    return Err(KymoraError::UnknownProfile {
                        profile: prof.to_string(),
                    });
                }
            }
        }

        let parsed_views: Vec<String> = if let Some(v_list) = views {
            let mut list = Vec::new();
            for v in v_list {
                let s = v.as_ref();
                if !views::SUPPORTED_VIEWS.contains(&s) {
                    return Err(KymoraError::UnknownProfile {
                        profile: format!("unsupported view '{s}'"),
                    });
                }
                list.push(s.to_string());
            }
            if list.is_empty() {
                vec!["raw".to_string()]
            } else {
                list
            }
        } else {
            vec!["raw".to_string()]
        };

        let mut items = Vec::new();
        let mut names = Vec::new();
        let mut active_needs = Needs::empty();

        let is_plain_raw = parsed_views.len() == 1 && parsed_views[0] == "raw";

        for v in &parsed_views {
            for &idx in &base_indices {
                let def = &FEATURES[idx];
                if !is_plain_raw && views::is_pruned(v, def.name, def.invariances) {
                    continue;
                }
                let output_name = if is_plain_raw {
                    def.name.to_string()
                } else {
                    format!("{v}__{}", def.name)
                };
                items.push(PlanItem {
                    view: v.clone(),
                    feature_idx: idx,
                    output_name: output_name.clone(),
                });
                names.push(output_name);
                active_needs |= def.needs;
            }
        }

        Ok(Self {
            indices: base_indices,
            names,
            needs: active_needs,
            items,
            views: parsed_views,
        })
    }

    #[inline]
    pub fn n_features(&self) -> usize {
        self.items.len()
    }
}
