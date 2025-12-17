"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./context/AuthContext";

export default function Home() {
  const { loading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    console.log('loading:',loading)
    if (loading) return;

    if (isAuthenticated) {
      
      router.replace("/dashboard");
    } else {
      console.log("not authenticated")
      router.replace("/landing-page");
    }
  }, [loading, isAuthenticated, router]);

  return null; 
}
