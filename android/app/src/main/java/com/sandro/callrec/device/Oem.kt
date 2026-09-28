package com.sandro.callrec.device

enum class Oem {
    MOTOROLA, SAMSUNG, XIAOMI, OPPO_FAMILY, HUAWEI, GOOGLE, OTHER;

    companion object {
        fun from(manufacturer: String, brand: String): Oem {
            val s = "$manufacturer $brand".lowercase()
            return when {
                "motorola" in s || "lenovo" in s -> MOTOROLA
                "samsung" in s -> SAMSUNG
                "xiaomi" in s || "redmi" in s || "poco" in s -> XIAOMI
                "oppo" in s || "oneplus" in s || "realme" in s -> OPPO_FAMILY
                "huawei" in s || "honor" in s -> HUAWEI
                "google" in s -> GOOGLE
                else -> OTHER
            }
        }
    }
}
