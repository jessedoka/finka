import { z } from "zod";

import { createTRPCRouter, publicProcedure } from "~/server/api/trpc";

export const accountRouter = createTRPCRouter({
  hello: publicProcedure
    .input(z.object({ text: z.string() }))
    .query(({ input }) => {
      return {
        greeting: `Hello ${input.text}`,
      };
    }),

  create: publicProcedure
    .input(z.object({ name: z.string().min(1) }))
    .mutation(async ({ ctx, input }) => {
      // simulate a slow db call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      return ctx.db.account.create({
        data: {
          name: input.name,
        },
      });
    }),

  getLatest: publicProcedure.query(({ ctx }) => {
      return ctx.db.account.findFirst({
        orderBy: {
          createdAt: "desc",
        },
      });
    }),

  getAll: publicProcedure.query(({ ctx }) => {
      return ctx.db.account.findMany();
    }),

  getById: publicProcedure
    .input(z.object({ id: z.number().optional() }))
    .query(({ ctx, input }) => {
      return ctx.db.account.findUnique({
        where: {
          id: input.id,
        },
      });
    }),

  update: publicProcedure
    .input(z.object({ id: z.number(), name: z.string().min(1) }))
    .mutation(({ ctx, input }) => {
      return ctx.db.account.update({
        where: {
          id: input.id,
        },
        data: {
          name: input.name,
        },
      });
    }),

  delete: publicProcedure
    .input(z.object({ id: z.number() }))
    .mutation(({ ctx, input }) => {
      return ctx.db.account.delete({
        where: {
          id: input.id,
        },
      });
    }),

  deleteAll: publicProcedure.mutation(({ ctx }) => {
      return ctx.db.account.deleteMany();
    }),
});
